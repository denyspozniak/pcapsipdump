#include <string.h>
#include <math.h>
#include <time.h>
#include <stdio.h>
#include <pcap.h>

#include "../../calltable.h"

// Normally defined in pcapsipdump.cpp, which the benchmark does not link in.
int verbosity = 0;

void populate_calltable(calltable *ct, int n_elements){
    // calltable::add() memcpy()s a fixed 16 bytes out of caller/callee,
    // so they have to be that wide here and not string literals.
    char caller[16] = "1000";
    char callee[16] = "2000";

    for (int i=1; i < n_elements; i++){
        char call_id[32];

        snprintf(call_id, sizeof(call_id), "%d", i);
        int call_idx = ct->add(call_id, strlen(call_id), caller, callee, (time_t)i);
        calltable_element *ce = &ct->table[call_idx];
        for (int j=0; j < calltable_max_ip_per_call; j++){
            ct->add_ip_port(ce, (in_addr_t) i, (unsigned short) (i + j));
        }
    }
}

float benchmark_find_ip_port_ssrc(calltable *ct, int iterations){
    calltable_element *ce = NULL;
    int idx_rtp;
    clock_t t1;
    t1 = clock();
    for(int i=0;i<iterations;i++){
        ct->find_ip_port_ssrc((in_addr_t)0, 0, 0, &ce, &idx_rtp);
    }
    return((float)(clock()-t1)*1000000.0/(float)(CLOCKS_PER_SEC)/float(iterations));

}

int main(void){
    calltable *ct;

    ct = new calltable;
    populate_calltable(ct,1);
    for(int i=1;i<6;i++){
        int n = int(pow(10,i)/2);
        int m = n - int(pow(10,i-1)/2);
        //printf("populating %d entries...\n", m);
        populate_calltable(ct,m);
        //printf("benchmarking over %d iterations...\n", 3*int(pow(10,5-i)));
        printf("%7.3f us per ct->find_ip_port_ssrc() with %d*%d elements in table\n",
                benchmark_find_ip_port_ssrc(ct,3*int(pow(10,5-i))),
                n,
                calltable_max_ip_per_call);
    }
    delete ct;
}
