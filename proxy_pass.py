from cryptography.fernet import Fernet

# Gerar uma chave de criptografia (faça isso uma vez e guarde a chave com segurança)
#key = Fernet.generate_key()
key = b'f9L0h2GPICnx-WRPMjzHQUD1TLrmjjGQ-kTiX9cqoX8='
cipher_suite = Fernet(key)

# Criptografar a senha
senha = "minha_senha_secreta"
senha_criptografada = cipher_suite.encrypt(senha.encode())

print(f"Senha criptografada: {senha_criptografada}")
print(f"Chave secreta (guarde isso!): {key}")

#################################3
cipher_suite = Fernet(key)
senha_descriptografada = cipher_suite.decrypt(senha_criptografada).decode()
print(f"Senha original: {senha_descriptografada}")
