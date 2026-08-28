#include <string.h>
#include <stdlib.h>
#include "pcapsipdump_strlib.h"

const char * gettag(const char *ptr, unsigned long len, const char *tag, unsigned long *gettaglen){
    unsigned long tl;
    const char *r, *lp;

    if(len > 1){
        tl = strlen(tag);
        // A tag only counts at the start of a line: either at the very
        // beginning of the buffer, or right after CR/LF. Starting the search
        // at ptr rather than ptr+1 is what makes the first case work.
        for(r = ptr; r != NULL && (unsigned long)(r - ptr) < len;){
            r = (const char*)memmem(r, len-(r-ptr), tag, tl);
            if(r == NULL){
                break;
            }
            if(r == ptr || r[-1] == '\r' || r[-1] == '\n') {
                r += tl;
                while (r < (ptr+len) && r[0] == ' ') {
                    r++;
                }
                for(lp = r; lp < (ptr+len); lp++){
                    if(*lp == '\r' || *lp == '\n'){
                        *gettaglen = lp - r;
                        return r;
                    }
                }
                // unterminated line: not a usable value, keep looking
            } else {
                r++;
            }
        }
    }
    *gettaglen = 0;
    return NULL;
}


uint8_t sdp_get_rtpmap_event(const char *sdp) {
    // a=rtpmap:101 telephone-event/8000
    uint32_t sdp_len = strlen(sdp);
    unsigned long l;
    const char *s;
    const char *te = " telephone-event/";
    int tel = strlen(te);

    s = gettag(sdp, sdp_len, "a=rtpmap:", &l);
    if (s && (strncmp(te, s + 1, tel) == 0 ||
              strncmp(te, s + 2, tel) == 0 ||
              strncmp(te, s + 3, tel) == 0 )) {
        l = atol(s);
        // the return type is uint8_t, so 256 and above cannot be represented
        if (l <= 255) {
            return l;
        }
    }
    return 0;
}

