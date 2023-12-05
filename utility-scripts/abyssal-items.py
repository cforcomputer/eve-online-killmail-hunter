from bs4 import BeautifulSoup

# Read the HTML content from the 'info_types.php' file with explicit encoding
with open('info_types.php', 'r', encoding='utf-8') as file:
    html_content = file.read()

# Parse the HTML content
soup = BeautifulSoup(html_content, 'html.parser')

# Find all rows with class "highlight" and check if the type contains the word "abyssal"
abyssal_rows = soup.find_all('tr', class_='highlight')

# Open a text file for writing
with open('output.txt', 'w', encoding='utf-8') as file:
    for row in abyssal_rows:
        type_published = row.find(class_=lambda x: x and 'type_published' in x)
        type_name = row.find(class_=lambda x: x and 'type_published' in x).find_next('td')

        if type_published and type_name and 'abyssal' in type_name.text.lower() and 'skin' not in type_name.text.lower():
            # Extract the number within border-right-grey
            number_within_border = type_published.text.strip()
            file.write(f"Type: {type_name.text.strip()}, Number within border-right-grey: {number_within_border}\n")

print("Numbers written to output.txt")
