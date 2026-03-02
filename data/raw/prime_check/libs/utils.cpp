#include "utils.h"

bool is_prime(int v){
    if(v == 2) return true;

    for(int i = 3; i * i <= v; i += 2){
        if(v % i) continue;
        return false;
    }

    return (v >= 2);
}