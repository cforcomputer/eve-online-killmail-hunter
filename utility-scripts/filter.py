import re

# Define your regular expression
regex_pattern = r'[0-9]+:'

# Input file path
input_file_path = 'blueprints.txt'

# Output file path
output_file_path = 'output.txt'

# Compile the regex pattern
regex = re.compile(regex_pattern)

# Function to filter and write matches to a new line
def filter_and_write_matches(input_text):
    matches = regex.findall(input_text)
    return '\n'.join(matches).replace(":", "")

# Read from input file and write to output file
with open(input_file_path, 'r') as input_file, open(output_file_path, 'w') as output_file:
    input_text = input_file.read()
    filtered_text = filter_and_write_matches(input_text)
    output_file.write(filtered_text)

print(f"Filtered content has been written to {output_file_path}")
