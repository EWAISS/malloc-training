#include <stdio.h>

int main() {
    char a = 'A';
    int b = 42;
    double c = 3.14;
    char d = 'Z';
    int e = 99;

    printf("a: address=%p  size=%zu\n", (void*)&a, sizeof(a));
    printf("b: address=%p  size=%zu\n", (void*)&b, sizeof(b));
    printf("c: address=%p  size=%zu\n", (void*)&c, sizeof(c));
    printf("d: address=%p  size=%zu\n", (void*)&d, sizeof(d));
    printf("e: address=%p  size=%zu\n", (void*)&e, sizeof(e));

    return 0;
}
