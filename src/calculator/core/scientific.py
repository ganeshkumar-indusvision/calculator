"""Scientific calculator for background jobs."""

import sys
from decimal import Decimal, localcontext

from src.calculator.core.calculator import Calculator

if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(0)

class ScientificCalculator(Calculator):
    """Calculator with slow operations that suit background jobs."""

    def __init__(self) -> None:
        super().__init__()
        # removed Decimal becuase very low performance (Not good for long heavy computation)
        # getcontext().prec = 1_000_000
        self.operations.update({"fact": (1,self.factorial),
                                "primes": (1,self.count_primes),
                                "fib": (1,self.fibonacci)})
        self.scientific_operations = {"fact","primes", "fib"}
        self.validation.update({
            "fact":self._check_fact,
            "primes": self._check_primes,
            "fib": self._check_fib
        })
        
    def _check_fact(self, n: int) -> None:
        if n < 0:
            raise ValueError("fact requires a non-negative number")
        if n > 200000:
            raise ValueError("fact is limited to n ≤ 200000")
    
    def factorial(self, num: int) -> Decimal:
        with localcontext(prec=1_000_000):
            fact = Decimal(str(1))
            value = Decimal(str(2))
        # fact = 1
        # value =2
            while(value <= num):
                fact *= value
                value +=1  
            return fact

    def _check_primes(self, n: int) -> None:
        if n < 2:
            raise ValueError("primes requires a non-negative number and should be greater than 2")
    def _check_fib(self, n: int) -> None:
        if n < 0:
            raise ValueError("fib requires a non-negative number")

    def fibonacci(self, num: int) -> Decimal:
        with localcontext(prec=1_000_000):
            num = int(num)
            result = Decimal(str(0))
            value = Decimal(str(1))
            # result = 0
            # value = 1
            for _ in range(num):
                result, value = value, result + value
            return result


    def count_primes(self, num: Decimal) -> tuple[Decimal, Decimal]:  # (count, largest)
        with localcontext(prec=1_000_000):
            num = int(num)
            prime = [True] * int(num+1)
            p = 2
            length = 0
            while (p*p<=num):
                if prime[p]:

                    for i in range(p*p,num+1,p):
                        prime[i]=False

                p+=1
            for i in range(2,num+1,1):
                if prime[i]:
                    last = i
                    length +=1 

            return  Decimal(str(length)),Decimal(str(last))
        # return length,last

    def _validate_output(self, op: str, *results: Decimal):
        if op in self.scientific_operations:
            if op == "primes":
                results = results[0]

            converted = tuple(int(value) for value in results)
            return converted[0] if len(converted) == 1 else converted

        return super()._validate_output(op, *results)

    def _validate_number(self, number: object, op: str) -> None:
        if op in {"fact", "fib"}:
            if not isinstance(number, int) or isinstance(number, bool):
                raise ValueError(f"{number!r} is not a valid integer")
            return

        super()._validate_number(number,op)
