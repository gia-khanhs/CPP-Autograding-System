#include "utils.h"

long long factorial(int v){
    if(v == 0 || v == 1) return 1;

    return v * factorial(v - 1);
}
