#!/usr/bin/env python3
"""Self-test of mccabe.py: sources whose complexity is known."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mccabe  # noqa: E402

JAVA = '''package demo;

import java.util.List;

@Service
public class Invoice {
    // if (comment) && ignored
    public Invoice() {
    }

    @GetMapping("/x")
    public int simple(String s) {
        String text = "if (a && b) { while }";
        return s.length();
    }

    public int discount(Customer c, List<Line> lines) throws Exception {
        int total = 0;
        for (Line l : lines) {
            if (l.price() > 0 && c.active() || c.vip()) {
                total += c.vip() ? 2 : 1;
            }
        }
        switch (c.type()) {
            case A: total++; break;
            case B: total--; break;
            default: break;
        }
        try {
            total++;
        } catch (RuntimeException e) {
            total = 0;
        }
        lines.forEach(l -> {
            if (l == null) { total2(); }
        });
        do { total++; } while (total < 3);
        return total;
    }

    static class Inner {
        boolean ok(Map<String, ?> m, int x) {
            while (x > 0) { x--; }
            return x == 0;
        }
    }
}
'''

TS = '''export class Cart {
  total?: number;

  constructor(private repo: Repo) {}

  async compute(lines: Line[], code?: string): Promise<number> {
    let t = this.total ?? 0;
    for (const l of lines) {
      if (l.price > 0 && code?.length) { t += l.price; }
    }
    return t > 10 ? t : 0;
  }

  readonly flatten = (xs: number[]): number => {
    return xs.length > 0 ? xs[0] : 0;
  };
}

export function standalone(a: number) {
  if (a) { return 1; }
  return 0;
}
'''


def by_name(reports):
    return {(r.name, m.name): m.complexity for r in reports for m in r.methods}


def check(label, actual, expected):
    status = "ok" if actual == expected else "FAIL"
    print(f"{status:6} {label}: expected {expected}, got {actual}")
    return actual == expected


def main():
    java = by_name(mccabe.analyse(JAVA, "java"))
    ts = by_name(mccabe.analyse(TS, "ts"))
    results = [
        check("Java constructor", java[("Invoice", "Invoice")], 1),
        check("Java string and comment ignored", java[("Invoice", "simple")], 1),
        # 1 + for + if + && + || + ternary + 2 case + catch + if (lambda) + while (do-while)
        check("Java discount", java[("Invoice", "discount")], 11),
        check("Java nested class, generic ? ignored", java[("Invoice.Inner", "ok")], 2),
        check("TS method (?? ?. for if && ternary)", ts[("Cart", "compute")], 6),
        check("TS constructor", ts[("Cart", "constructor")], 1),
        check("TS class arrow function", ts[("Cart", "flatten")], 2),
        check("TS top-level function", ts[("(top-level functions)", "standalone")], 2),
    ]
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
