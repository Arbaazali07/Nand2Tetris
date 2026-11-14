import os
import sys
import re


def create_symbol_table():

    symbols = {
        "SP": 0,
        "LCL": 1,
        "ARG": 2,
        "THIS": 3,
        "THAT": 4,
        "SCREEN": 16384,
        "KBD": 24576
    }

    for i in range(16):
        symbols[f"R{i}"] = i

    return symbols


def is_valid_symbol(symbol):

    pattern = r'^[A-Za-z_.$:][A-Za-z0-9_.$:]*$'

    return bool(re.match(pattern, symbol))


def first_pass(lines, symbols):

    instructions = []
    labels = set()
    rom_address = 0

    for line_number, line in enumerate(lines, start=1):

        line = line.split("//")[0].strip()

        if not line:
            continue

        line = re.sub(r'\s+', '', line)

        if line.startswith("(") or line.endswith(")"):

            if not (line.startswith("(") and line.endswith(")")):
                raise ValueError(
                    f"Line {line_number}: Invalid label declaration"
                )

            label = line[1:-1]

            if not label:
                raise ValueError(
                    f"Line {line_number}: Empty label"
                )

            if not is_valid_symbol(label):
                raise ValueError(
                    f"Line {line_number}: Invalid label name '{label}'"
                )

            if label in symbols or label in labels:
                raise ValueError(
                    f"Line {line_number}: Duplicate or reserved label '{label}'"
                )

            symbols[label] = rom_address
            labels.add(label)

        else:

            instructions.append((line, line_number))
            rom_address += 1

    return instructions, labels


def second_pass(instructions, symbols, labels):

    machine_code = []
    variables = set()
    next_variable = 16

    comp_table = {
        "0": "0101010",
        "1": "0111111",
        "-1": "0111010",
        "D": "0001100",
        "A": "0110000",
        "M": "1110000",
        "!D": "0001101",
        "!A": "0110001",
        "!M": "1110001",
        "-D": "0001111",
        "-A": "0110011",
        "-M": "1110011",
        "D+1": "0011111",
        "A+1": "0110111",
        "M+1": "1110111",
        "D-1": "0001110",
        "A-1": "0110010",
        "M-1": "1110010",
        "D+A": "0000010",
        "D+M": "1000010",
        "D-A": "0010011",
        "D-M": "1010011",
        "A-D": "0000111",
        "M-D": "1000111",
        "D&A": "0000000",
        "D&M": "1000000",
        "D|A": "0010101",
        "D|M": "1010101"
    }

    dest_table = {
    "": "000",
    "M": "001",
    "D": "010",
    "MD": "011",
    "DM": "011",
    "A": "100",
    "AM": "101",
    "MA": "101",
    "AD": "110",
    "DA": "110",
    "AMD": "111",
    "ADM": "111",
    "AMD": "111",
    "MAD": "111",
    "MDA": "111",
    "DAM": "111",
    "DMA": "111"
}

    jump_table = {
        "": "000",
        "JGT": "001",
        "JEQ": "010",
        "JGE": "011",
        "JLT": "100",
        "JNE": "101",
        "JLE": "110",
        "JMP": "111"
    }

    for instruction, line_number in instructions:

        try:

            if instruction.startswith("@"):

                value = instruction[1:]

                if not value:
                    raise ValueError("Empty A-instruction")

                if value.isdigit():

                    address = int(value)

                else:

                    if not is_valid_symbol(value):
                        raise ValueError(
                            f"Invalid symbol name '{value}'"
                        )

                    if value not in symbols:

                        if next_variable > 16383:
                            raise ValueError(
                                "Variable memory limit exceeded"
                            )

                        symbols[value] = next_variable
                        variables.add(value)
                        next_variable += 1

                    address = symbols[value]

                if not 0 <= address <= 32767:
                    raise ValueError("Address out of range")

                binary = format(address, "016b")

                machine_code.append(binary)

            else:

                dest = ""
                jump = ""
                comp = instruction

                if "=" in comp:

                    if comp.count("=") != 1:
                        raise ValueError(
                            "Invalid destination instruction"
                        )

                    dest, comp = comp.split("=")

                if ";" in comp:

                    if comp.count(";") != 1:
                        raise ValueError(
                            "Invalid jump instruction"
                        )

                    comp, jump = comp.split(";")

                if dest not in dest_table:
                    raise ValueError(
                        f"Invalid destination '{dest}'"
                    )

                if comp not in comp_table:
                    raise ValueError(
                        f"Invalid computation '{comp}'"
                    )

                if jump not in jump_table:
                    raise ValueError(
                        f"Invalid jump '{jump}'"
                    )

                binary = (
                    "111"
                    + comp_table[comp]
                    + dest_table[dest]
                    + jump_table[jump]
                )

                machine_code.append(binary)

        except ValueError as error:

            raise ValueError(
                f"Line {line_number}: {error}"
            ) from error

    return machine_code, labels, variables


def save_symbols(symbols, labels, variables, output_folder):

    filename = os.path.join(output_folder, "symbols.txt")

    with open(filename, "w", encoding="utf-8") as file:

        file.write("HACK ASSEMBLER SYMBOL TABLE\n\n")

        file.write("LABELS (ROM ADDRESSES)\n")

        for label in sorted(labels, key=lambda x: symbols[x]):
            file.write(f"{label} = {symbols[label]}\n")

        file.write("\nVARIABLES (RAM ADDRESSES)\n")

        for variable in sorted(variables, key=lambda x: symbols[x]):
            file.write(f"{variable} = {symbols[variable]}\n")

    print("symbols.txt generated successfully!")


def assemble(input_file):

    if not os.path.isfile(input_file):
        raise FileNotFoundError(
            f"Assembly file not found: {input_file}"
        )

    with open(input_file, "r", encoding="utf-8") as file:
        lines = file.readlines()

    symbols = create_symbol_table()

    print("\nHack Assembler Started")

    instructions, labels = first_pass(lines, symbols)

    print("First pass completed.")
    print("Labels identified:", len(labels))

    machine_code, labels, variables = second_pass(
        instructions,
        symbols,
        labels
    )

    print("Second pass completed.")
    print("Instructions converted:", len(machine_code))

    output_file = os.path.splitext(input_file)[0] + ".hack"

    with open(output_file, "w", encoding="utf-8") as file:

        file.write("\n".join(machine_code))

        if machine_code:
            file.write("\n")

    print("Machine code saved:", output_file)

    output_folder = os.path.dirname(
        os.path.abspath(input_file)
    )

    save_symbols(
        symbols,
        labels,
        variables,
        output_folder
    )

    print("\nAssembly Summary")
    print("----------------")
    print("Roll Number:", "2501410039")
    print("Personal K:", 39)
    print("K mod 3:", 0)
    print("Labels:", len(labels))
    print("Variables:", len(variables))
    print("Instructions:", len(machine_code))
    print("Personal feature: symbols.txt generated")
    print("\nAssembly completed successfully!")


if __name__ == "__main__":

    if len(sys.argv) > 1:
        input_file = sys.argv[1]

    else:
        input_file = input(
            "Enter assembly file name: "
        ).strip()

    try:
        assemble(input_file)

    except FileNotFoundError as error:
        print("Error:", error)

    except ValueError as error:
        print("Assembler Error:", error)

    except PermissionError:
        print("Error: Permission denied.")

    except Exception as error:
        print("Unexpected Error:", error)