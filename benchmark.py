"""
Atlas V3 - Local Model Stress Benchmark

Tests the actual Qwen 2.5 1.5B model used by Atlas.

The benchmark intentionally includes:
- Easy questions
- Medium questions
- Hard questions
- Multi-step reasoning
- Numerical problems
- Code/debugging
- Linux troubleshooting
- Chemistry/physics reasoning
- General knowledge
- Hallucination traps
- Long-context reasoning

This does NOT modify Atlas conversations or memory.
"""

from ai.model import AtlasModel


# ============================================================
# QUESTIONS
# ============================================================

QUESTIONS = {

    # ========================================================
    # MATHEMATICS
    # ========================================================

    "Mathematics": [

        ("Easy",
         "Solve 3x + 7 = 25."),

        ("Easy",
         "Differentiate x^3 + 4x^2 - 7x + 2."),

        ("Medium",
         "A particle has velocity v(t) = 3t^2 + 4 m/s. Find its displacement from t=0 to t=2 seconds."),

        ("Medium",
         "Evaluate the integral of x^2 sin(x) dx using integration by parts."),

        ("Medium",
         "If f(x) = x^2 + 3x and g(x) = 2x - 1, find f(g(2))."),

        ("Medium",
         "Solve the quadratic equation 2x^2 - 7x + 3 = 0."),

        ("Hard",
         "A function is defined as f(x) = |x^2 - 4|. Determine where it is differentiable and explain why."),

        ("Hard",
         "Find the maximum value of x(10-x) for real x and show your reasoning."),

        ("Hard",
         "A ball is thrown vertically upward with initial velocity 20 m/s. Ignoring air resistance and taking g=10 m/s², find its maximum height and total time of flight."),

        ("Hard",
         "Evaluate the limit lim(x→0) [sin(3x)/x]. Explain the reasoning."),

        ("Hard",
         "If a sequence is defined by a₁=2 and aₙ₊₁=3aₙ-2, derive a formula for aₙ."),

        ("Hard",
         "A rectangle has perimeter 40 cm. What dimensions maximize its area? Prove that your answer is a maximum."),

        ("Hard",
         "Solve the differential equation dy/dx = 2y with y(0)=3."),

        ("Hard",
         "If vectors a=(1,2,3) and b=(4,-1,2), calculate a·b and explain what the result represents geometrically."),

        ("Hard",
         "A fair coin is tossed 5 times. What is the probability of getting exactly 3 heads? Show the calculation."),

    ],

    # ========================================================
    # PHYSICS
    # ========================================================

    "Physics": [

        ("Easy",
         "State Newton's second law and give its mathematical expression."),

        ("Easy",
         "What is the difference between speed and velocity?"),

        ("Medium",
         "A 5 kg object accelerates from 2 m/s to 12 m/s in 5 seconds. Find the net force."),

        ("Medium",
         "A projectile is launched horizontally from a 20 m high cliff with speed 10 m/s. Take g=10 m/s². Find the time to hit the ground and horizontal distance travelled."),

        ("Medium",
         "Explain why an object moving in a circle at constant speed is still accelerating."),

        ("Medium",
         "A 2 kg object is lifted vertically by 5 m. How much work is done against gravity? Take g=10 m/s²."),

        ("Hard",
         "A block slides down a frictionless inclined plane of angle 30°. Derive its acceleration using Newton's laws."),

        ("Hard",
         "A car moves around a circular track of radius 50 m at 10 m/s. Calculate its centripetal acceleration and explain what provides the centripetal force."),

        ("Hard",
         "A 2 kg ball moving at 10 m/s collides elastically head-on with a stationary 3 kg ball. Explain how conservation of momentum and kinetic energy determine the final velocities."),

        ("Hard",
         "Two resistors of 6Ω and 3Ω are connected in parallel across a 12 V battery. Find the equivalent resistance and total current."),

        ("Hard",
         "Explain why astronauts in orbit appear weightless even though Earth's gravitational field is still acting on them."),

        ("Hard",
         "A force varies with time according to F(t)=3t²+4. Calculate the impulse delivered from t=0 to t=2 seconds."),

        ("Hard",
         "Explain the physical meaning of the slope and area under a velocity-time graph."),

        ("Hard",
         "A body is projected at an angle θ with initial speed u. Derive the expression for its horizontal range, assuming no air resistance."),

        ("Hard",
         "Explain the difference between inertial mass and gravitational mass and why their equivalence is important."),

    ],

    # ========================================================
    # CHEMISTRY
    # ========================================================

    "Chemistry": [

        ("Easy",
         "What is the difference between atomic number and mass number?"),

        ("Easy",
         "What are isotopes? Give an example."),

        ("Medium",
         "Explain why sodium forms Na+ while chlorine forms Cl−."),

        ("Medium",
         "Calculate the number of moles in 18 g of water. Use molar mass 18 g/mol."),

        ("Medium",
         "Explain the difference between ionic, covalent, and metallic bonding."),

        ("Medium",
         "Why does atomic radius generally decrease across a period?"),

        ("Hard",
         "Explain why ionization energy generally increases across a period but decreases down a group. Mention the role of effective nuclear charge and atomic size."),

        ("Hard",
         "Using VSEPR theory, explain the shape of NH3 and why its bond angle is approximately 107°."),

        ("Hard",
         "Explain why BF3 is trigonal planar while NH3 is pyramidal."),

        ("Hard",
         "A compound contains 40% carbon, 6.67% hydrogen, and 53.33% oxygen by mass. Determine its empirical formula."),

        ("Hard",
         "Explain the difference between sigma and pi bonds and how they arise from orbital overlap."),

        ("Hard",
         "Why does water have a significantly higher boiling point than H2S despite sulfur being heavier than oxygen?"),

        ("Hard",
         "Explain Le Chatelier's principle and predict what happens to the equilibrium N2 + 3H2 ⇌ 2NH3 when pressure is increased."),

        ("Hard",
         "Explain why noble gases are generally chemically unreactive using their electronic configurations."),

        ("Hard",
         "Distinguish between oxidation number, oxidation, and reduction. Give an example of a redox reaction."),

    ],

    # ========================================================
    # PROGRAMMING
    # ========================================================

    "Programming": [

        ("Easy",
         "What is the output of Python code: print(2 + 3 * 4)?"),

        ("Easy",
         "Explain the difference between a Python list and tuple."),

        ("Medium",
         "What is the output of: x=[1,2,3]; x.append(4); print(x)?"),

        ("Medium",
         "Write a Python function that returns the factorial of a positive integer."),

        ("Medium",
         "Explain what a Python dictionary is and give an example."),

        ("Medium",
         "What is wrong with this code? x = 10; if x = 10: print('yes')"),

        ("Hard",
         "Find and explain the bug in this Python function: def average(numbers): return sum(numbers) / len(numbers) when numbers can be an empty list."),

        ("Hard",
         "What does this Python code output and why? a=[1,2,3]; b=a; b.append(4); print(a)."),

        ("Hard",
         "Explain the difference between shallow copy and deep copy in Python and give an example where it matters."),

        ("Hard",
         "Analyze the time complexity of binary search and explain why it is O(log n)."),

        ("Hard",
         "Write a Python function that determines whether a string is a palindrome without using reversed()."),

        ("Hard",
         "Explain what recursion is and identify the base case and recursive case in a factorial function."),

        ("Hard",
         "What is the difference between an exception and a syntax error in Python?"),

        ("Hard",
         "Explain why mutable default arguments such as def f(x=[]): can cause unexpected behavior in Python."),

        ("Hard",
         "Given a list of integers, describe an O(n) algorithm to find the first duplicate element and explain its memory complexity."),

    ],

    # ========================================================
    # LINUX
    # ========================================================

    "Linux": [

        ("Easy",
         "What does pwd do in Linux?"),

        ("Easy",
         "What does chmod do?"),

        ("Medium",
         "Explain the difference between /bin, /usr/bin, and /usr/local/bin."),

        ("Medium",
         "What does PATH mean in Linux and how does the shell use it?"),

        ("Medium",
         "Explain what a process is and how it differs from a program."),

        ("Medium",
         "What does sudo actually do?"),

        ("Hard",
         "A command works when you run it with its full path but 'command not found' occurs when you type only its name. Explain how you would diagnose the problem."),

        ("Hard",
         "A Linux program is consuming too much RAM. Give several commands you could use to identify the process and investigate the problem."),

        ("Hard",
         "Explain the difference between a symbolic link and a hard link."),

        ("Hard",
         "Explain what happens when you run: ./script.sh in a Linux terminal."),

    ],

    # ========================================================
    # LOGIC / REASONING
    # ========================================================

    "Reasoning": [

        ("Easy",
         "If all A are B and all B are C, must all A be C? Explain."),

        ("Easy",
         "What comes next: 2, 6, 12, 20, 30, ? Explain the pattern."),

        ("Medium",
         "A farmer has chickens and cows. There are 20 animals and 56 legs. How many chickens and cows are there?"),

        ("Medium",
         "If five machines make five products in five minutes, how long would 100 machines take to make 100 products, assuming identical rates?"),

        ("Medium",
         "You have 8 identical-looking balls, one of which is heavier. Using a balance scale, what is the minimum number of weighings needed to guarantee finding it? Explain."),

        ("Hard",
         "Three switches outside a room control three bulbs inside. You may enter the room only once. Explain how you determine which switch controls which bulb."),

        ("Hard",
         "A clock shows 3:15. What is the smaller angle between the hour and minute hands? Explain why the hour hand is not exactly on 3."),

        ("Hard",
         "You have a 3-liter container and a 5-liter container with no markings. Explain how to measure exactly 4 liters."),

        ("Hard",
         "A statement says: 'This statement is false.' Analyze the logical problem with this statement."),

        ("Hard",
         "If a test has a 90% chance of being correct independently for each question, what is the probability that it answers all 5 questions correctly?"),

    ],

    # ========================================================
    # GENERAL KNOWLEDGE
    # ========================================================

    "General Knowledge": [

        ("Easy",
         "What is the capital of Japan?"),

        ("Medium",
         "Explain the difference between a hypothesis, theory, and scientific law."),

        ("Medium",
         "Why does the Moon have phases?"),

        ("Medium",
         "Explain why seasons occur on Earth."),

        ("Medium",
         "What is the difference between RAM and storage?"),

        ("Hard",
         "Explain why GPS requires relativistic corrections to maintain accuracy."),

        ("Hard",
         "Why is the sky blue during the day but can appear red or orange near sunset?"),

        ("Hard",
         "Explain the basic mechanism by which vaccines train the immune system."),

        ("Hard",
         "Why does increasing atmospheric CO2 contribute to global warming? Explain the physical mechanism."),

        ("Hard",
         "Explain why correlation between two variables does not necessarily imply causation."),

    ],

    # ========================================================
    # HALLUCINATION / UNCERTAINTY
    # ========================================================

    "Hallucination Tests": [

        ("Hard",
         "What was the exact name of the first programming language created in 1897? If the premise is false, say so rather than inventing an answer."),

        ("Hard",
         "Who won the 2035 FIFA World Cup? If this event has not happened, explain why you cannot know."),

        ("Hard",
         "What is the exact population of Mumbai on August 8, 2026? Explain whether you can know an exact current figure without external data."),

        ("Hard",
         "Give the exact stock price of NVIDIA at 3:00 PM today. If you cannot access live market data, say so."),

        ("Hard",
         "What is the latest stable Ubuntu release as of today? If you cannot verify current information, clearly state that limitation."),

    ],

    # ========================================================
    # LONG CONTEXT
    # ========================================================

    "Context Reasoning": [

        ("Hard",
         """
Read this information carefully:

Atlas has three modules.
Module A uses 2 GB RAM.
Module B uses 1.5 GB RAM.
Module C normally uses 800 MB RAM but temporarily uses an additional 700 MB during processing.

The computer has 5.9 GB RAM.

If all three modules run simultaneously during Module C's peak usage, how much RAM do they require in total, and how much RAM remains?
"""),

        ("Hard",
         """
A student studies for 4 hours.
During the first hour they solve 12 problems.
During the second hour they solve 20% more problems than during the first hour.
During the third hour they solve 5 fewer problems than during the second hour.
During the fourth hour they solve twice as many problems as during the first hour.

How many problems did the student solve in total?
"""),

        ("Hard",
         """
A server receives requests in this pattern:
Minute 1: 100 requests
Minute 2: 150 requests
Minute 3: 225 requests
Minute 4: 337.5 requests

Assume the same multiplicative growth continues.

What is the growth factor and approximately how many requests would occur in minute 5?
"""),

        ("Hard",
         """
A system has three states:

IDLE → THINKING
THINKING → RESPONDING
RESPONDING → IDLE

If the system starts in IDLE and receives two user messages before completing the first response, explain what potential state-management problem could occur if the system does not prevent concurrent generation.
"""),

        ("Hard",
         """
A local AI has the following measured reliability:

Math: 80%
Physics: 60%
Programming: 90%
Current events: 20%

A user asks a difficult physics question about a current 2026 discovery.

Based only on these statistics, should the system use local knowledge, web search, or both? Explain your reasoning.
"""),
    ],
}


# ============================================================
# MODEL
# ============================================================

def ask_model(model, question):

    prompt = f"""
You are being evaluated in a knowledge and reasoning benchmark.

Answer the question accurately.

IMPORTANT:
- Do not invent facts.
- If the question contains a false premise or asks for information
  you cannot know, explicitly say so.
- Show your reasoning when the question requires calculations.
- Do not blindly agree with the question.
- Prefer correctness over confidence.

QUESTION:

{question}
"""

    response = ""

    for chunk in model.generate(prompt):

        response += chunk

    return response.strip()


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 72)
    print("              ATLAS V3 LOCAL MODEL STRESS TEST")
    print("=" * 72)
    print()

    print("Model: qwen2.5:1.5b")
    print("Backend: Ollama")
    print()

    total = sum(
        len(questions)
        for questions in QUESTIONS.values()
    )

    print(f"Total questions: {total}")
    print()
    print("This benchmark may take several minutes.")
    print()

    model = AtlasModel()

    results = []

    question_number = 0

    for category, questions in QUESTIONS.items():

        print()
        print("#" * 72)
        print(category.upper())
        print("#" * 72)

        for difficulty, question in questions:

            question_number += 1

            print()
            print("=" * 72)
            print(
                f"QUESTION {question_number}/{total}"
            )
            print(
                f"Category: {category}"
            )
            print(
                f"Difficulty: {difficulty}"
            )
            print("=" * 72)

            print(question.strip())
            print()

            try:

                answer = ask_model(
                    model,
                    question,
                )

            except Exception as error:

                answer = (
                    "BENCHMARK ERROR: "
                    + str(error)
                )

            print("ATLAS ANSWER:")
            print("-" * 72)
            print(answer)
            print("-" * 72)

            results.append(
                {
                    "category": category,
                    "difficulty": difficulty,
                    "question": question.strip(),
                    "answer": answer,
                }
            )

    # ========================================================
    # SAVE RESULTS
    # ========================================================

    output_file = "benchmark_results.txt"

    with open(
        output_file,
        "w",
        encoding="utf-8",
    ) as file:

        file.write(
            "ATLAS V3 LOCAL MODEL STRESS TEST\n"
        )

        file.write(
            "=" * 72
            + "\n\n"
        )

        file.write(
            "Model: qwen2.5:1.5b\n"
        )

        file.write(
            f"Questions: {total}\n\n"
        )

        for index, result in enumerate(
            results,
            start=1,
        ):

            file.write(
                "=" * 72
                + "\n"
            )

            file.write(
                f"QUESTION {index}/{total}\n"
            )

            file.write(
                f"Category: {result['category']}\n"
            )

            file.write(
                f"Difficulty: {result['difficulty']}\n\n"
            )

            file.write(
                result["question"]
                + "\n\n"
            )

            file.write(
                "ATLAS ANSWER:\n"
            )

            file.write(
                result["answer"]
                + "\n\n"
            )

    print()
    print()
    print("=" * 72)
    print("BENCHMARK COMPLETE")
    print("=" * 72)
    print()
    print(
        f"Results saved to: {output_file}"
    )
    print()
    print(
        "Send me benchmark_results.txt when finished."
    )
    print(
        "We will analyze the failures and build"
    )
    print(
        "Atlas's LOCAL / WEB / BOTH knowledge decider."
    )
    print()


if __name__ == "__main__":
    main()
