/**
 * @file cebir.h
 * @brief Custom non-commutative algebra with elements {1, h, q, -1, -h, -q}.
 * 
 * Algebra Multiplication Table:
 *   ⋅ |  1 |  h |  q
 *  ---+----+----+----
 *   1 |  1 |  h |  q
 *   h |  h |  q |  1
 *   q |  q | -1 |  q
 * 
 * Supports negative signs and full operator overloads: *, *=, ==, !=, - (unary), and stream I/O.
 */

#ifndef CEBIR_H
#define CEBIR_H

#include <iostream>
#include <string>
#include <stdexcept>
#include <ostream>

class Cebir {
public:
    enum class ElementVal {
        ONE,      //  1
        H,        //  h
        Q,        //  q
        NEG_ONE,  // -1
        NEG_H,    // -h
        NEG_Q     // -q
    };

private:
    ElementVal val;

    // Helper to get the absolute/positive base of an element
    static ElementVal get_base(ElementVal v) {
        switch (v) {
            case ElementVal::NEG_ONE: return ElementVal::ONE;
            case ElementVal::NEG_H:   return ElementVal::H;
            case ElementVal::NEG_Q:   return ElementVal::Q;
            default:                  return v;
        }
    }

    // Helper to check if an element is negative
    static bool is_negative(ElementVal v) {
        return (v == ElementVal::NEG_ONE || v == ElementVal::NEG_H || v == ElementVal::NEG_Q);
    }

    // Helper to create an element from base and sign
    static ElementVal make_element(ElementVal base, bool is_neg) {
        ElementVal clean_base = get_base(base);
        if (is_neg) {
            switch (clean_base) {
                case ElementVal::ONE: return ElementVal::NEG_ONE;
                case ElementVal::H:   return ElementVal::NEG_H;
                case ElementVal::Q:   return ElementVal::NEG_Q;
                default:              return clean_base;
            }
        } else {
            return clean_base;
        }
    }

public:
    // Constructors
    Cebir() : val(ElementVal::ONE) {}
    Cebir(ElementVal v) : val(v) {}

    // Getter for the internal value
    ElementVal getValue() const { return val; }

    // Unary minus operator (negation)
    Cebir operator-() const {
        return Cebir(make_element(val, !is_negative(val)));
    }

    // Unary plus operator (noop)
    Cebir operator+() const {
        return *this;
    }

    // Multiplication operator overload
    Cebir operator*(const Cebir& rhs) const {
        bool lhs_neg = is_negative(this->val);
        bool rhs_neg = is_negative(rhs.val);
        bool result_neg = lhs_neg ^ rhs_neg;

        ElementVal lhs_base = get_base(this->val);
        ElementVal rhs_base = get_base(rhs.val);

        ElementVal res_base;
        if (lhs_base == ElementVal::ONE) {
            res_base = rhs_base;
        } else if (lhs_base == ElementVal::H) {
            if (rhs_base == ElementVal::ONE) res_base = ElementVal::H;
            else if (rhs_base == ElementVal::H) res_base = ElementVal::Q;
            else res_base = ElementVal::ONE; // h * q = 1
        } else { // lhs_base == ElementVal::Q
            if (rhs_base == ElementVal::ONE) res_base = ElementVal::Q;
            else if (rhs_base == ElementVal::H) res_base = ElementVal::NEG_ONE; // q * h = -1
            else res_base = ElementVal::Q; // q * q = q (Projection operator detail)
        }

        // Apply sign factoring in any sign inside res_base
        bool res_base_is_neg = is_negative(res_base);
        bool final_neg = result_neg ^ res_base_is_neg;

        return Cebir(make_element(res_base, final_neg));
    }

    // Multiplication-assignment operator
    Cebir& operator*=(const Cebir& rhs) {
        *this = *this * rhs;
        return *this;
    }

    // Equality comparison
    bool operator==(const Cebir& rhs) const {
        return this->val == rhs.val;
    }

    // Inequality comparison
    bool operator!=(const Cebir& rhs) const {
        return !(*this == rhs);
    }

    // Convert to string for display
    std::string toString() const {
        switch (val) {
            case ElementVal::ONE:     return "1";
            case ElementVal::H:       return "h";
            case ElementVal::Q:       return "q";
            case ElementVal::NEG_ONE: return "-1";
            case ElementVal::NEG_H:   return "-h";
            case ElementVal::NEG_Q:   return "-q";
            default:                  return "?";
        }
    }

    // Static helper to create elements easily
    static Cebir one() { return Cebir(ElementVal::ONE); }
    static Cebir h() { return Cebir(ElementVal::H); }
    static Cebir q() { return Cebir(ElementVal::Q); }
    static Cebir neg_one() { return Cebir(ElementVal::NEG_ONE); }
    static Cebir neg_h() { return Cebir(ElementVal::NEG_H); }
    static Cebir neg_q() { return Cebir(ElementVal::NEG_Q); }

    /**
     * @brief Calculates the power of the element (h^n).
     * Since this algebra is non-associative, the order of multiplication matters.
     * @param exponent The non-negative integer exponent.
     * @param left_associative If true, calculates as (...((x * x) * x) ... * x).
     *                         If false, calculates as (x * (x * ... (x * x)...)).
     */
    Cebir power(int exponent, bool left_associative = true) const {
        if (exponent < 0) {
            throw std::invalid_argument("Negative exponents are not defined for this algebra.");
        }
        if (exponent == 0) {
            return Cebir::one();
        }
        if (exponent == 1) {
            return *this;
        }

        if (left_associative) {
            Cebir result = *this;
            for (int i = 1; i < exponent; ++i) {
                result = result * *this;
            }
            return result;
        } else {
            // Right-associative: x * (x * ... * (x * x))
            return *this * power(exponent - 1, false);
        }
    }

    // Overload of operator^ to calculate power (defaults to left-associative)
    // NOTE: In C++, operator^ has a lower precedence than operator*, so use parentheses: (h ^ 2) * q
    Cebir operator^(int exponent) const {
        return power(exponent, true);
    }
};

// Stream insertion operator
inline std::ostream& operator<<(std::ostream& os, const Cebir& c) {
    os << c.toString();
    return os;
}

#endif // CEBIR_H
