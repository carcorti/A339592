/* Bounded test fixture: expose the candidate's graph bits, no run state. */
#define main candidate_main
#include "../src/a339592.c"
#undef main
int main(void){
    init_powers();
    for(unsigned i=2;i<=MAX_N;++i){
        for(unsigned j=1;j<i;++j)putchar(edge(i,j)?'1':'0');
        putchar('\n');
    }
    return 0;
}
