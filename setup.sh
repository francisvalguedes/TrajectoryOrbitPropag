mkdir -p ~/.streamlit/
echo "\
[general]\n\
email = \"francisval.guedes.soares.037@ufrn.edu.br\"\n\
" > ~/.streamlit/credentials.toml
echo "\
[server]\n\
headless = true\n\
enableCORS=false\n\
port = $PORT\n\
" > ~/.streamlit/config.toml