"""
Script to generate demo fixture files (synthetic, public-domain content).
Run with: python tests/fixtures/generate_fixtures.py
"""
from __future__ import annotations

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def create_text_fixture(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    print(f"Created: {path}")


def create_pdf_fixture(path: Path, title: str, content: str) -> None:
    """Create a simple PDF using reportlab if available, else skip."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.units import inch

        doc = SimpleDocTemplate(str(path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph(title, styles["Title"]))
        story.append(Spacer(1, 0.3 * inch))

        for para in content.split("\n\n"):
            if para.strip():
                story.append(Paragraph(para.strip(), styles["BodyText"]))
                story.append(Spacer(1, 0.1 * inch))

        doc.build(story)
        print(f"Created PDF: {path}")
    except ImportError:
        # Fallback: create a text file instead
        text_path = path.with_suffix(".txt")
        text_path.write_text(f"{title}\n\n{content}", encoding="utf-8")
        print(f"(reportlab not available) Created text fallback: {text_path}")


def main() -> None:
    fixtures = Path(__file__).parent

    # ──────────────────────────────────────────────
    # 1. Operating Systems notes
    # ──────────────────────────────────────────────
    os_content = """Operating Systems — Study Notes

Chapter 1: Introduction to Operating Systems

An operating system (OS) is system software that manages computer hardware and software
resources and provides common services for computer programs.

Chapter 2: Processes

A process is a program in execution. Each process has its own memory space, program counter,
registers, and stack. Processes are isolated from one another to prevent interference.

Process States:
- New: The process is being created.
- Running: Instructions are being executed.
- Waiting: The process is waiting for some event (I/O completion).
- Ready: The process is waiting to be assigned to a CPU.
- Terminated: The process has finished execution.

Process Control Block (PCB):
The OS maintains a PCB for each process containing: process state, process ID, program counter,
CPU registers, CPU scheduling information, memory management information, accounting information,
I/O status information.

Chapter 3: Threads

A thread is the smallest unit of execution within a process. Threads within the same process
share memory and resources. Multi-threading allows concurrent execution within a process.

Types of threads:
- User-level threads: managed by user-space libraries without kernel support.
- Kernel-level threads: managed directly by the operating system.

Chapter 4: CPU Scheduling

CPU scheduling is the mechanism by which the operating system decides which process runs on
the CPU at any given time.

Common scheduling algorithms:
- First Come First Served (FCFS): processes are scheduled in order of arrival.
- Shortest Job Next (SJN): the process with the smallest burst time runs first.
- Round Robin (RR): each process gets a fixed time quantum.
- Priority Scheduling: processes with higher priority run first.

Scheduling metrics:
- Throughput: number of processes completed per unit time.
- Turnaround time: total time from submission to completion.
- Waiting time: time spent in the ready queue.
- Response time: time from submission to first response.

Chapter 5: Memory Management

Memory management is the function of an OS that handles the management of primary memory.

Virtual memory allows the execution of processes that are not completely in memory.
Paging is a memory management scheme that eliminates the need for contiguous allocation.
A page table maps virtual addresses to physical addresses.

Page faults occur when a program accesses a page not currently in physical memory.
The OS must load the required page from disk (page-in) to service the fault.

Replacement algorithms:
- FIFO: replace the oldest page.
- LRU: replace the least recently used page.
- Optimal: replace the page that won't be used for the longest time.

Chapter 6: File Systems

A file system controls how data is stored and retrieved on storage devices.
Files are organized into directories (folders) in a hierarchical tree structure.
Common file systems: FAT32, NTFS (Windows), ext4 (Linux), APFS (macOS).

File operations: create, open, read, write, seek, close, delete.
File attributes: name, type, location, size, timestamps, permissions.
"""

    create_text_fixture(fixtures / "sample_operating_systems.txt", os_content)
    try:
        create_pdf_fixture(
            fixtures / "sample_operating_systems.pdf",
            "Operating Systems — Study Notes",
            os_content,
        )
    except Exception as e:
        print(f"  PDF creation skipped: {e}")

    # ──────────────────────────────────────────────
    # 2. Discrete Mathematics notes
    # ──────────────────────────────────────────────
    math_content = """Discrete Mathematics — Study Notes

Chapter 1: Sets

A set is a well-defined collection of distinct objects called elements or members.
Notation: A = {1, 2, 3, 4, 5}

Set operations:
- Union (A ∪ B): elements in A, B, or both.
- Intersection (A ∩ B): elements in both A and B.
- Difference (A − B): elements in A but not B.
- Complement (A'): elements not in A (within the universal set).
- Power set P(A): set of all subsets of A.

Chapter 2: Relations

A relation R from set A to set B is a subset of A × B (the Cartesian product).
A binary relation on set A is a subset of A × A.

Properties of relations:
- Reflexive: aRa for all a in A.
- Symmetric: if aRb then bRa for all a, b in A.
- Transitive: if aRb and bRc then aRc for all a, b, c in A.
- Antisymmetric: if aRb and bRa then a=b.

An equivalence relation is reflexive, symmetric, and transitive.
A partial order is reflexive, antisymmetric, and transitive.

Chapter 3: Functions

A function f: A → B assigns to each element of A exactly one element of B.
- Domain: the set A.
- Codomain: the set B.
- Range: the set of all actual output values.

Types of functions:
- Injective (one-to-one): distinct inputs map to distinct outputs.
- Surjective (onto): every element in B has at least one preimage.
- Bijective: both injective and surjective (a perfect pairing).

Chapter 4: Graph Theory

A graph G = (V, E) consists of a set of vertices V and a set of edges E.

Types of graphs:
- Undirected graph: edges have no direction.
- Directed graph (digraph): edges have direction.
- Weighted graph: edges have associated weights.
- Complete graph Kn: every pair of vertices is connected.

Graph terminology:
- Degree: number of edges incident to a vertex.
- Path: sequence of vertices connected by edges.
- Cycle: a path that starts and ends at the same vertex.
- Connected graph: there is a path between every pair of vertices.
- Tree: a connected acyclic graph.

Chapter 5: Logic

Propositional logic deals with propositions that are either true or false.

Logical connectives:
- Negation (¬p): NOT p
- Conjunction (p ∧ q): p AND q
- Disjunction (p ∨ q): p OR q
- Implication (p → q): if p then q
- Biconditional (p ↔ q): p if and only if q

Logical equivalences:
- De Morgan's Laws: ¬(p ∧ q) ≡ ¬p ∨ ¬q and ¬(p ∨ q) ≡ ¬p ∧ ¬q
- Double negation: ¬¬p ≡ p
- Contrapositive: p → q ≡ ¬q → ¬p

Chapter 6: Proof Techniques

Direct proof: assume the hypothesis and derive the conclusion logically.
Proof by contradiction: assume the negation and derive a contradiction.
Proof by induction: base case + inductive step.
- Base case: prove P(1) is true.
- Inductive step: assume P(k) is true, prove P(k+1) is true.
"""

    create_text_fixture(fixtures / "sample_discrete_math.txt", math_content)
    try:
        create_pdf_fixture(
            fixtures / "sample_discrete_math.pdf",
            "Discrete Mathematics — Study Notes",
            math_content,
        )
    except Exception as e:
        print(f"  PDF creation skipped: {e}")

    # ──────────────────────────────────────────────
    # 3. Python programming notes
    # ──────────────────────────────────────────────
    python_content = """Python Programming — Study Notes

Chapter 1: Data Types

Python has several built-in data types:
- int: integer numbers (e.g., 42, -7)
- float: floating-point numbers (e.g., 3.14)
- str: text strings (e.g., "Hello, world!")
- bool: boolean values (True or False)
- list: ordered, mutable sequence (e.g., [1, 2, 3])
- tuple: ordered, immutable sequence (e.g., (1, 2, 3))
- dict: key-value pairs (e.g., {"name": "Alice", "age": 20})
- set: unordered collection of unique elements (e.g., {1, 2, 3})

Chapter 2: Control Flow

if statements:
  if condition:
      # execute if True
  elif other_condition:
      # execute if other_condition is True
  else:
      # execute otherwise

for loops iterate over a sequence:
  for item in collection:
      # process item

while loops execute while condition is True:
  while condition:
      # execute

List comprehensions provide concise list creation:
  squares = [x**2 for x in range(10)]

Chapter 3: Functions

def function_name(parameters):
    # function body
    return value

Default parameters allow optional arguments:
  def greet(name, greeting="Hello"):
      return f"{greeting}, {name}!"

*args and **kwargs allow variable arguments:
  def func(*args, **kwargs):
      pass

Lambda functions are anonymous single-expression functions:
  square = lambda x: x ** 2

Chapter 4: Object-Oriented Programming

class MyClass:
    def __init__(self, value):
        self.value = value

    def method(self):
        return self.value

Inheritance:
  class Child(Parent):
      def __init__(self):
          super().__init__()

Chapter 5: Error Handling

try:
    risky_operation()
except ValueError as e:
    handle_value_error(e)
except (TypeError, KeyError) as e:
    handle_other_errors(e)
finally:
    cleanup()

Chapter 6: File I/O

with open("file.txt", "r") as f:
    content = f.read()

with open("output.txt", "w") as f:
    f.write("Hello, file!")
"""

    create_text_fixture(fixtures / "sample_python_notes.txt", python_content)

    print("\n✅ All fixtures generated successfully.")


if __name__ == "__main__":
    main()
