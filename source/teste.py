# import streamlit as st

# mypag = [
#         st.Page("mypages/03_map.py", title="Create your account"),
#         st.Page("mypages/00_Simplified.py", title="Manage your account"),
#     ]

# pg = st.navigation(mypag)
# pg.run()

import streamlit as st

# Define our pages
def home():
    st.title("Home Page")
    st.write("Welcome to the home page!")
    if st.button("Go to Hidden Page"):
        st.switch_page(st.Page(page=hidden_page, title="Hidden page", icon=":material/home:"))


def about():
    st.title("About Page")
    st.write("This is the about page.")


def hidden_page():
    st.title("Hidden Page")
    st.write("This page is not in the navigation!")


# Main app
def main():
    # Define the pages
    pages = {
        "Main": [
            st.Page(page=home, title="Home", icon=":material/home:", default=True),
            st.Page(page="pages/00_Simplified.py", title="About", icon=":material/home:"),
            # st.Page(page=hidden_page, title="Hidden page", icon=":material/home:"), # TODO[SB]: Uncomment this line to check if it works then
        ]
    }

    # Use st.navigation to create the navigation
    selected_page = st.navigation(pages, position="sidebar")

    # Run the selected page
    selected_page.run()

if __name__ == "__main__":
    main()