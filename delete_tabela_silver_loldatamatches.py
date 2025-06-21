import sqlite3


# Conecta ao banco
conexao = sqlite3.connect("lol_datamatches.db")
cursor = conexao.cursor()

# Deleta a tabela
cursor.execute('''
               drop table if exists match_data_silver
               ''')
# Fecha a conexão
conexao.close()