from bs4 import BeautifulSoup

# Read home.html 
with open('./home.html', 'r') as html_file:
    content = html_file.read()
    # print(content)

    # Create new instance of BeautifulSoup with the content and parser
    soup = BeautifulSoup(content, 'lxml')
    courses_html_tags = soup.find_all('h5')

    # Print all course titles
    # for course in courses_html_tags:
    #     print(course.text)

    courses_cards = soup.find_all('div', class_='card')
    for course in courses_cards:
        course_name = course.h5.text
        course_price = course.a.text.split()[-1] # Split to tokens and take the last toke in the collection

        print(f'{course_name} costs {course_price}')
