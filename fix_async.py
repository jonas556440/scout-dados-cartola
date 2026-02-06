
import re

file_path = '/root/cartolafc2026/api_server.py'

with open(file_path, 'r') as f:
    content = f.read()

# Substituir 'async def' por 'def' APENAS onde não há await dentro (já verifiquei que não há await no arquivo todo)
# Mas vamos substituir 'async def' por 'def'
new_content = re.sub(r'async def ', 'def ', content)

with open(file_path, 'w') as f:
    f.write(new_content)

print("Substituídos todos os 'async def' por 'def' com sucesso.")
