#ifndef CONST_H
#define CONST_H

#ifdef __ASSEMBLY__
#define UL(address) (address)
#define ULL(address) (address)
#else
#define UL(address) (addressUL)
#define ULL(address) (addressULL)
#endif

#endif
