#define _GNU_SOURCE
/*
MIT License

Copyright (c) 2026 Carlo Corti

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

*/
/* A339592: all independent subsets of MG_n, including the empty set.
 * Project owner: Carlo Corti (identity: confirmed project strategy).
 * C17 with GCC/Clang unsigned __int128, Linux/POSIX file operations.
 * Public package source: a339592.c.
 * MG_n edge i>j iff [z^(i-j-1)] M(z)^j is odd, M=1+zM+z^2M^2.
 * Deletion partitions independent sets by absence/presence of a vertex.
 * Every six consecutive vertices induce at most 15 independent sets;
 * count <= 15^32 < 2^128 for n<=192 (eight starting residues mod 8).
 * All induced-state counts inject into full-graph counts; checked U128 sums.
 * Even an unexpected edgeless state of size>=128 fails rather than wraps.
 * Term-boundary recovery only. A term exceeding 3500 seconds needs reassessment.
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <inttypes.h>
#include <string.h>
#include <errno.h>
#include <signal.h>
#include <time.h>
#include <unistd.h>
#include <fcntl.h>
#include <dirent.h>
#include <sys/stat.h>
#include <sys/file.h>
#ifndef __SIZEOF_INT128__
#error "128-bit integer support required"
#endif
#ifndef SOURCE_SHA
#error "Build with the canonical Makefile"
#endif
__extension__ typedef unsigned __int128 U128;
typedef struct { uint64_t lo, hi, top; } Mask;
typedef struct { Mask key; U128 value; } Entry;
_Static_assert(sizeof(Entry)==48, "cache size contract");
#define MAX_N 192U
#define SLOTS (1U<<20)
#define TEXT_CAP 16384U
#define SEGMENT_SECONDS 3500.0
static Mask adj[MAX_N];
static Entry *cache;
static size_t slots=SLOTS;
static volatile sig_atomic_t stopped;
static uint64_t calls, hits;
static int saturated, arithmetic_error;
static double started, heartbeat;
static unsigned current_n;
static int timed;
static unsigned clock_ticks;
static const unsigned known[]={2,3,4,7,9,13,17,26,29,48,55,95};
_Noreturn static void die(const char *s) { fprintf(stderr,"ERROR: %s (%s)\n",s,strerror(errno)); exit(1); }
static double now(void) { struct timespec t; if(clock_gettime(CLOCK_MONOTONIC,&t)) die("clock"); return (double)t.tv_sec+(double)t.tv_nsec/1e9; }
static void signal_stop(int sig) { (void)sig; stopped=1; }
static void inc(uint64_t *v) { if(*v==UINT64_MAX) saturated=1; else ++*v; }
/* All bit/first callers obey 0<=v<MAX_N and nonempty masks. */
static Mask bit(unsigned v) {
    if(v<64) return (Mask){UINT64_C(1)<<v,0,0};
    if(v<128) return (Mask){0,UINT64_C(1)<<(v-64),0};
    return (Mask){0,0,UINT64_C(1)<<(v-128)};
}
static Mask join(Mask a,Mask b){return (Mask){a.lo|b.lo,a.hi|b.hi,a.top|b.top};}
static Mask full(unsigned n){Mask s={0,0,0};for(unsigned i=0;i<n;++i)s=join(s,bit(i));return s;}
static Mask intersect(Mask a,Mask b){return (Mask){a.lo&b.lo,a.hi&b.hi,a.top&b.top};}
static Mask without(Mask a,Mask b){return (Mask){a.lo&~b.lo,a.hi&~b.hi,a.top&~b.top};}
static unsigned pop(Mask s){return (unsigned)__builtin_popcountll(s.lo)+(unsigned)__builtin_popcountll(s.hi)+(unsigned)__builtin_popcountll(s.top);}
static unsigned first(Mask s){if(s.lo)return (unsigned)__builtin_ctzll(s.lo);if(s.hi)return 64U+(unsigned)__builtin_ctzll(s.hi);return 128U+(unsigned)__builtin_ctzll(s.top);}
static int equal(Mask a,Mask b){return a.lo==b.lo && a.hi==b.hi && a.top==b.top;}
/* Coefficients of M and successive powers of M over GF(2), truncated at 191.
 * b_k=b_(k-1) xor [k even, k>=2] b_((k-2)/2).
 * This follows by Frobenius from M=1+zM+z^2M^2. */
static unsigned char powers[MAX_N+1][MAX_N];
static void init_powers(void){
    unsigned char b[MAX_N]={0};
    b[0]=1;
    for(unsigned k=1;k<MAX_N;++k){
        b[k]=b[k-1];
        if(k>=2 && !(k&1U))b[k]^=b[(k-2)/2];
    }
    powers[0][0]=1;
    for(unsigned j=1;j<=MAX_N;++j){
        for(unsigned d=0;d<MAX_N;++d){
            unsigned char x=0;
            for(unsigned t=0;t<=d;++t)x^=(unsigned char)(powers[j-1][d-t]&b[t]);
            powers[j][d]=x;
        }
    }
}
static int edge(unsigned i,unsigned j){return powers[j][i-j-1]!=0;}

static void graph(unsigned n){
    memset(adj,0,sizeof adj);
    for(unsigned i=2;i<=n;++i)for(unsigned j=1;j<i;++j)if(edge(i,j)){
        adj[i-1]=join(adj[i-1],bit(j-1));adj[j-1]=join(adj[j-1],bit(i-1));
    }
}
static size_t hashmask(Mask s){uint64_t x=s.lo^(s.hi*UINT64_C(0x9e3779b97f4a7c15))^(s.top*UINT64_C(0xd6e8feb86659fd93));x^=x>>30;x*=UINT64_C(0xbf58476d1ce4e5b9);x^=x>>27;x*=UINT64_C(0x94d049bb133111eb);x^=x>>31;return (size_t)(x&(slots-1));}
static U128 count(Mask s){
    if(stopped || arithmetic_error) return 0;
    inc(&calls);
    clock_ticks=(clock_ticks+1U)&4095U;
    if(timed && clock_ticks==0){double t=now();if(t-started>=SEGMENT_SECONDS){stopped=1;return 0;}if(t-heartbeat>=5){fprintf(stderr,"ACTIVE n=%u calls=%" PRIu64 " hits=%" PRIu64 " elapsed=%.0f s saturated=%d\n",current_n,calls,hits,t-started,saturated);heartbeat=t;}}
    if(!(s.lo|s.hi|s.top))return 1;
    size_t slot=slots?hashmask(s):0;
    if(slots && equal(cache[slot].key,s)){inc(&hits);return cache[slot].value;}
    Mask scan=s;unsigned v=0,degree=0;
    while(scan.lo|scan.hi|scan.top){unsigned u=first(scan);scan=without(scan,bit(u));unsigned d=pop(intersect(s,adj[u]));if(d>degree){degree=d;v=u;}}
    U128 value;
    if(!degree){unsigned k=pop(s);if(k>=128){arithmetic_error=1;return 0;}value=(U128)1<<k;}
    else {Mask b=bit(v),closed=join(adj[v],b);U128 a=count(without(s,b));if(stopped||arithmetic_error)return 0;U128 c=count(without(s,closed));if(stopped||arithmetic_error)return 0;if(~(U128)0-a<c){arithmetic_error=1;return 0;}value=a+c;}
    if(slots)cache[slot]=(Entry){s,value};
    return value;
}
static void decimal(U128 n,char out[40]){char rev[40];size_t k=0;do{rev[k++]=(char)('0'+(unsigned)(n%10));n/=10;}while(n);for(size_t i=0;i<k;++i)out[i]=rev[k-i-1];out[k]=0;}
static int number(const char *s,U128 *out){if(!*s || (*s=='0' && s[1]))return 0;U128 v=0;for(;*s;++s){if(*s<'0'||*s>'9')return 0;unsigned d=(unsigned)(*s-'0');if(v>(~(U128)0-d)/10)return 0;v=v*10+d;}*out=v;return 1;}
/* SHA-256; unsigned arithmetic is modulo 2^32. Streaming input < 2^61 bytes. */
typedef struct {uint32_t h[8];unsigned char b[64];size_t used;uint64_t bytes;} Sha;
static uint32_t rotr(uint32_t x,unsigned n){return (x>>n)|(x<<(32-n));}
static void block(Sha *s){
static const uint32_t k[64]={0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
uint32_t w[64];for(unsigned i=0;i<16;++i)w[i]=((uint32_t)s->b[4*i]<<24)|((uint32_t)s->b[4*i+1]<<16)|((uint32_t)s->b[4*i+2]<<8)|s->b[4*i+3];for(unsigned i=16;i<64;++i){uint32_t x=w[i-15],y=w[i-2];w[i]=w[i-16]+(rotr(x,7)^rotr(x,18)^(x>>3))+w[i-7]+(rotr(y,17)^rotr(y,19)^(y>>10));}
uint32_t a=s->h[0],b=s->h[1],c=s->h[2],d=s->h[3],e=s->h[4],f=s->h[5],g=s->h[6],h=s->h[7];for(unsigned i=0;i<64;++i){uint32_t t=h+(rotr(e,6)^rotr(e,11)^rotr(e,25))+((e&f)^(~e&g))+k[i]+w[i];uint32_t u=(rotr(a,2)^rotr(a,13)^rotr(a,22))+((a&b)^(a&c)^(b&c));h=g;g=f;f=e;e=d+t;d=c;c=b;b=a;a=t+u;}s->h[0]+=a;s->h[1]+=b;s->h[2]+=c;s->h[3]+=d;s->h[4]+=e;s->h[5]+=f;s->h[6]+=g;s->h[7]+=h;
}
static Sha sha_init(void){return (Sha){{0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19},{0},0,0};}
static void sha_add(Sha *s,const void *data,size_t n){const unsigned char *p=data;if(n>UINT64_MAX/8-s->bytes)die("SHA input too large");s->bytes+=n;while(n){size_t c=64-s->used;if(c>n)c=n;memcpy(s->b+s->used,p,c);s->used+=c;p+=c;n-=c;if(s->used==64){block(s);s->used=0;}}}
static void sha_end(Sha *s,char out[65]){uint64_t bits=s->bytes*8;s->b[s->used++]=128;if(s->used>56){memset(s->b+s->used,0,64-s->used);block(s);s->used=0;}memset(s->b+s->used,0,56-s->used);for(unsigned i=0;i<8;++i)s->b[63-i]=(unsigned char)(bits>>(8*i));block(s);for(unsigned i=0;i<8;++i)(void)sprintf(out+8*i,"%08" PRIx32,s->h[i]);}
static void digest(const void *p,size_t n,char out[65]){Sha s=sha_init();sha_add(&s,p,n);sha_end(&s,out);}
static void executable_hash(char out[65]){int fd=open("/proc/self/exe",O_RDONLY|O_CLOEXEC);if(fd<0)die("open executable");Sha s=sha_init();unsigned char b[4096];ssize_t n;while((n=read(fd,b,sizeof b))>0)sha_add(&s,b,(size_t)n);if(n<0)die("read executable");if(close(fd))die("close executable");sha_end(&s,out);}
static void write_all(int fd,const char *p,size_t n){while(n){ssize_t k=write(fd,p,n);if(k<0&&errno==EINTR)continue;if(k<=0)die("write");p+=k;n-=(size_t)k;}}
static size_t read_text(int dir,const char *name,char *b,size_t cap){int fd=openat(dir,name,O_RDONLY|O_NOFOLLOW|O_NONBLOCK|O_CLOEXEC);if(fd<0)die("open state");struct stat st;if(fstat(fd,&st)||!S_ISREG(st.st_mode)||st.st_nlink!=1)die("state is not a private regular file");size_t used=0;for(;;){if(used==cap-1)die("state too large");ssize_t n=read(fd,b+used,cap-1-used);if(n<0&&errno==EINTR)continue;if(n<0)die("read state");if(!n)break;used+=(size_t)n;}if(close(fd))die("close state");if(memchr(b,0,used))die("NUL in state");b[used]=0;return used;}
static void create_file(int dir,const char *name,const char *s){int fd=openat(dir,name,O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);if(fd<0)die("create state without clobber");write_all(fd,s,strlen(s));if(fsync(fd))die("sync file");if(close(fd))die("close file");if(fsync(dir))die("sync directory");}
static void meta_text(unsigned n,const char *binary,char out[2048]){int k=snprintf(out,2048,"{\"schema\":1,\"sequence\":\"A339592\",\"target\":%u,\"source_sha256\":\"%s\",\"make_sha256\":\"%s\",\"binary_sha256\":\"%s\",\"segment_seconds\":3500}\n",n,SOURCE_SHA,MAKE_SHA,binary);if(k<0||k>=2048)die("metadata overflow");}
static void snapshot(const U128 rows[MAX_N+1],unsigned done,const char *meta,char out[TEXT_CAP]){char mh[65],hash[65];digest(meta,strlen(meta),mh);int z=snprintf(out,TEXT_CAP,"# A339592 schema=1 meta_sha256=%s\n",mh);if(z<0)die("format state");size_t used=(size_t)z;for(unsigned n=1;n<=done;++n){char v[40];decimal(rows[n],v);z=snprintf(out+used,TEXT_CAP-used,"%u\t%s\n",n,v);if(z<0||(size_t)z>=TEXT_CAP-used)die("snapshot capacity");used+=(size_t)z;}digest(out,used,hash);z=snprintf(out+used,TEXT_CAP-used,"# sha256=%s\n",hash);if(z<0||(size_t)z>=TEXT_CAP-used)die("checksum capacity");}
static unsigned load_rows(int dir,unsigned target,const char *meta,U128 rows[MAX_N+1]){char raw[TEXT_CAP],copy[TEXT_CAP],expected[TEXT_CAP];read_text(dir,"run.tsv",raw,sizeof raw);memcpy(copy,raw,strlen(raw)+1);char *p=strchr(copy,'\n');if(!p)die("missing header");++p;unsigned done=0;while(*p && *p!='#'){char *end=strchr(p,'\n'),*tab=strchr(p,'\t');if(!end||!tab||tab>end||done>=target)die("malformed row");*tab=0;*end=0;U128 index,value;if(!number(p,&index)||index!=done+1U||!number(tab+1,&value)||!value)die("invalid indexed count");++done;rows[done]=value;if(done<=12 && value!=known[done-1])die("known prefix mismatch");p=end+1;}snapshot(rows,done,meta,expected);if(strcmp(raw,expected))die("noncanonical or corrupt snapshot");return done;}
static void commit(int dir,const U128 rows[MAX_N+1],unsigned done,const char *meta){char text[TEXT_CAP];snapshot(rows,done,meta,text);create_file(dir,"run.tmp",text);if(renameat(dir,"run.tmp",dir,"run.tsv"))die("atomic replacement");if(fsync(dir))die("sync replacement directory");}
/* Persist the directory entry too; syncing its children alone is insufficient. */
static void new_directory(const char *path){
    char *copy=strdup(path);if(!copy)die("directory path allocation");
    char *slash=strrchr(copy,'/');const char *parent=".";char *base=copy;
    if(slash){*slash=0;base=slash+1;parent=slash==copy?"/":copy;}
    if(!*base || !strcmp(base,".") || !strcmp(base,".."))die("invalid new directory basename");
    int pfd=open(parent,O_RDONLY|O_DIRECTORY|O_CLOEXEC);if(pfd<0)die("open new directory parent");
    if(mkdirat(pfd,base,0700))die("run requires a new directory");
    if(fsync(pfd))die("sync new directory parent");
    if(close(pfd))die("close new directory parent");
    free(copy);
}
static int directory(const char *path,int fresh){if(fresh)new_directory(path);int fd=open(path,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);if(fd<0)die("open run directory");if(flock(fd,LOCK_EX|LOCK_NB))die("run directory busy");DIR *d=fdopendir(dup(fd));if(!d)die("directory scan");struct dirent *e;errno=0;while((e=readdir(d))){if(!strcmp(e->d_name,".")||!strcmp(e->d_name,".."))continue;if(fresh || (strcmp(e->d_name,"meta.json")&&strcmp(e->d_name,"run.tsv")&&strcmp(e->d_name,"run.tmp")))die("unexpected directory entry");}if(errno)die("directory read");if(closedir(d))die("close directory scan");return fd;}
/* A safe regular run.tmp is an uncommitted row snapshot.  verify inspects it
 * without mutation; resume discards it only after the same type/link check. */
static int temp_present(int dir){struct stat s;if(fstatat(dir,"run.tmp",&s,AT_SYMLINK_NOFOLLOW)){if(errno==ENOENT)return 0;die("temporary state stat");}if(!S_ISREG(s.st_mode)||s.st_nlink!=1)die("unsafe temporary state");return 1;}
static void discard_temp(int dir){if(!temp_present(dir))return;if(unlinkat(dir,"run.tmp",0)||fsync(dir))die("discard uncommitted temporary state");}
static int test_fail(unsigned line){fprintf(stderr,"SELFTEST FAIL line %u\n",line);return 1;}
static int selftest(void){
 /* Independently inspect finite six-block certificate at each residue mod 8. */
 static const unsigned block_counts[8]={13,14,13,14,15,12,14,15};
 graph(MAX_N);
 for(unsigned r=0;r<8;++r){
     Mask six={0,0,0};
     for(unsigned v=r;v<r+6;++v)six=join(six,bit(v));
     if(count(six)!=block_counts[r])return test_fail(__LINE__);
 }
 for(unsigned i=2;i<=MAX_N;++i){
     if(!edge(i,i-1))return test_fail(__LINE__);
     for(unsigned j=2;j<i;j+=2)if(!(i&1U)&&edge(i,j))return test_fail(__LINE__);
 }
 for(unsigned vtx=0;vtx<MAX_N;++vtx){
     Mask one=bit(vtx);if(pop(one)!=1||first(one)!=vtx)return test_fail(__LINE__);
     if(pop(without(full(MAX_N),one))!=MAX_N-1)return test_fail(__LINE__);
 }
 if(equal(bit(0),join(bit(0),bit(128))))return test_fail(__LINE__);

 char h[65],v[40];U128 u;digest("abc",3,h);if(strcmp(h,"ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"))return test_fail(__LINE__);decimal(~(U128)0,v);if(strcmp(v,"340282366920938463463374607431768211455")||!number(v,&u)||u!=~(U128)0)return test_fail(__LINE__);if(number("340282366920938463463374607431768211456",&u)||number("01",&u)||number("-1",&u))return test_fail(__LINE__);
 for(unsigned n=0;n<=MAX_N;++n)if(pop(full(n))!=n)return test_fail(__LINE__);
 for(unsigned n=1;n<=12;++n){graph(n);memset(cache,0,SLOTS*sizeof *cache);if(count(full(n))!=known[n-1])return test_fail(__LINE__);}
 for(unsigned n=1;n<=16;++n){graph(n);slots=0;U128 a=count(full(n));slots=1;memset(cache,0,sizeof *cache);if(count(full(n))!=a)return test_fail(__LINE__);}slots=SLOTS;
 memset(adj,0,sizeof adj);memset(cache,0,SLOTS*sizeof *cache);if(count(full(127))!=((U128)1<<127))return test_fail(__LINE__);if(count(full(128))!=0||!arithmetic_error)return test_fail(__LINE__);arithmetic_error=0;
 /* Third-word cache-key and degree traversal, using tiny induced states. */
 memset(adj,0,sizeof adj);adj[0]=bit(191);adj[191]=bit(0);slots=1;memset(cache,0,sizeof *cache);
 if(count(bit(191))!=2 || count(join(bit(0),bit(191)))!=3)return test_fail(__LINE__);
 slots=SLOTS;memset(adj,0,sizeof adj);memset(cache,0,SLOTS*sizeof *cache);
 if(count(full(MAX_N))!=0||!arithmetic_error)return test_fail(__LINE__);
 arithmetic_error=0;
 /* 129 vertices, two disjoint edges: branch values fit, their sum does not. */
 memset(adj,0,sizeof adj);adj[0]=bit(1);adj[1]=bit(0);adj[2]=bit(3);adj[3]=bit(2);
 memset(cache,0,SLOTS*sizeof *cache);
 if(count(full(129))!=0||!arithmetic_error)return test_fail(__LINE__);
 arithmetic_error=0;
 /* Exercise the exact production cooperative deadline path. */
 started=now()-SEGMENT_SECONDS-1;timed=1;clock_ticks=4095;
 if(count(bit(191))!=0||!stopped)return test_fail(__LINE__);
 stopped=0;timed=0;clock_ticks=0;
 char text[TEXT_CAP],meta[2048];U128 rows[MAX_N+1]={0};
 meta_text(MAX_N,"0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",meta);
 for(unsigned n=1;n<=MAX_N;++n)rows[n]=~(U128)0;
 snapshot(rows,MAX_N,meta,text);if(strlen(text)<8192)return test_fail(__LINE__);
 uint64_t counter=UINT64_MAX;inc(&counter);if(counter!=UINT64_MAX||!saturated)return test_fail(__LINE__);
 puts("SELFTEST PASS: SHA, uint128, mask 0..192, known 1..12, cache off/collision 1..16, overflow rejection, eight six-block counts, third-word keys, 192-row serialization");return 0;
}
int main(int argc,char **argv){
 int fresh=argc==4&&!strcmp(argv[1],"run"),resume=argc==3&&!strcmp(argv[1],"resume"),verify=argc==3&&!strcmp(argv[1],"verify"),test=argc==2&&!strcmp(argv[1],"selftest");U128 parsed=0;
 if(!(fresh||resume||verify||test)||(fresh&&(!number(argv[2],&parsed)||parsed<1||parsed>MAX_N))){fprintf(stderr,"Usage: a339592 run N NEW_DIR | resume DIR | verify DIR | selftest\nN=1..192; verify checks integrity, not independent enumeration.\n");return 2;}
 init_powers();
 if(!verify){cache=calloc(SLOTS,sizeof *cache);if(!cache)die("cache allocation");}
 if(test){int result=selftest();free(cache);return result;}
 struct sigaction sa;memset(&sa,0,sizeof sa);sa.sa_handler=signal_stop;sigemptyset(&sa.sa_mask);if(sigaction(SIGINT,&sa,NULL)||sigaction(SIGTERM,&sa,NULL))die("signal setup");
 char binary[65],meta[2048],raw[2048];executable_hash(binary);unsigned target=(unsigned)parsed,done=0;U128 rows[MAX_N+1]={0};int dir=directory(argv[fresh?3:2],fresh);
 if(fresh){meta_text(target,binary,meta);create_file(dir,"meta.json",meta);commit(dir,rows,0,meta);}
 else {read_text(dir,"meta.json",raw,sizeof raw);const char *key="{\"schema\":1,\"sequence\":\"A339592\",\"target\":";size_t off=strlen(key);if(strncmp(raw,key,off))die("foreign metadata");char *end=strchr(raw+off,',');if(!end || (size_t)(end-(raw+off))>3)die("invalid target");char ntext[4]={0};memcpy(ntext,raw+off,(size_t)(end-(raw+off)));if(!number(ntext,&parsed)||parsed<1||parsed>MAX_N)die("metadata target range");target=(unsigned)parsed;meta_text(target,binary,meta);if(strcmp(meta,raw))die("foreign build or noncanonical metadata");done=load_rows(dir,target,meta,rows);}
 if(verify){int pending=temp_present(dir);if(printf("INTEGRITY PASS rows=%u target=%u state=%s pending_tmp=%s; independent mathematical validation required\n",done,target,done==target?"COMPLETE":"PARTIAL",pending?"present":"none")<0||fflush(stdout))die("write integrity verdict");if(close(dir))die("close directory");return 0;}
 discard_temp(dir);started=heartbeat=now();timed=1;
 for(unsigned n=done+1;n<=target;++n){if(stopped||now()-started>=SEGMENT_SECONDS){stopped=1;break;}current_n=n;fprintf(stderr,"START n=%u completed_rows=%u\n",n,done);double term_started=now();graph(n);memset(cache,0,SLOTS*sizeof *cache);calls=hits=0;saturated=0;U128 value=count(full(n));if(arithmetic_error)die("count overflow");if(stopped)break;if(n<=12&&value!=known[n-1])die("known result mismatch");rows[n]=value;commit(dir,rows,n,meta);done=n;fprintf(stderr,"COMMITTED n=%u calls=%" PRIu64 " hits=%" PRIu64 " elapsed=%.6f s term_seconds=%.9f saturated=%d\n",n,calls,hits,now()-started,now()-term_started,saturated);}
 fprintf(stderr,"%s rows=%u target=%u elapsed=%.6f s; unfinished term is recomputed on resume\n",done==target?"COMPLETE":"PARTIAL",done,target,now()-started);free(cache);if(close(dir))die("close directory");return done==target?0:3;
}
