import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt


id_registro_edicao = None


def conectar():
    return sqlite3.connect("colina_burguers_financeiro.db")


def criar_tabela():
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lancamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            categoria TEXT NOT NULL,
            valor REAL NOT NULL,
            data TEXT NOT NULL
        )
    """)

    conexao.commit()
    conexao.close()


def validar_campos():
    descricao = entrada_descricao.get()
    categoria = entrada_categoria.get()
    valor = entrada_valor.get()

    if descricao == "" or descricao == "Ex: Venda de hambúrguer":
        messagebox.showwarning("Atenção", "Preencha a descrição.")
        return None

    if categoria == "" or categoria == "Ex: Vendas, Ingredientes, Bebidas":
        messagebox.showwarning("Atenção", "Preencha a categoria.")
        return None

    if valor == "" or valor == "Ex: 50,00":
        messagebox.showwarning("Atenção", "Preencha o valor.")
        return None

    try:
        valor = float(valor.replace(",", "."))
    except:
        messagebox.showerror("Erro", "Digite um valor válido. Exemplo: 50,00")
        return None

    return descricao, categoria, valor


def salvar_lancamento(tipo):
    global id_registro_edicao

    if id_registro_edicao is not None:
        messagebox.showwarning(
            "Atenção",
            "Você está editando um registro. Clique em 'Salvar Alteração' ou em 'Limpar Campos'."
        )
        return

    dados = validar_campos()
    if dados is None:
        return

    descricao, categoria, valor = dados

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        INSERT INTO lancamentos (tipo, descricao, categoria, valor, data)
        VALUES (?, ?, ?, ?, ?)
    """, (
        tipo,
        descricao,
        categoria,
        valor,
        datetime.now().strftime("%d/%m/%Y %H:%M")
    ))

    conexao.commit()
    conexao.close()

    limpar_campos()
    carregar_lancamentos()
    gerar_relatorio()

    messagebox.showinfo("Sucesso", f"{tipo} registrada com sucesso!")


def carregar_para_edicao():
    global id_registro_edicao

    selecionado = tabela.selection()

    if not selecionado:
        messagebox.showwarning("Atenção", "Selecione um registro na tabela para editar.")
        return

    id_registro_edicao = selecionado[0]

    item = tabela.item(id_registro_edicao)
    valores = item["values"]

    tipo = valores[0]
    descricao = valores[1]
    categoria = valores[2]
    valor = str(valores[3]).replace("R$", "").strip()

    entrada_descricao.delete(0, tk.END)
    entrada_categoria.delete(0, tk.END)
    entrada_valor.delete(0, tk.END)

    entrada_descricao.insert(0, descricao)
    entrada_categoria.insert(0, categoria)
    entrada_valor.insert(0, valor)

    entrada_descricao.config(fg="black")
    entrada_categoria.config(fg="black")
    entrada_valor.config(fg="black")

    label_status.config(
        text=f"Editando registro selecionado ({tipo}). Altere os dados e clique em Salvar Alteração.",
        fg="#e67e22"
    )


def salvar_alteracao():
    global id_registro_edicao

    if id_registro_edicao is None:
        messagebox.showwarning("Atenção", "Nenhum registro foi selecionado para edição.")
        return

    dados = validar_campos()
    if dados is None:
        return

    descricao, categoria, valor = dados

    resposta = messagebox.askyesno(
        "Confirmar Alteração",
        "Deseja realmente salvar as alterações deste registro?"
    )

    if not resposta:
        return

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        UPDATE lancamentos
        SET descricao = ?, categoria = ?, valor = ?
        WHERE id = ?
    """, (
        descricao,
        categoria,
        valor,
        id_registro_edicao
    ))

    conexao.commit()
    conexao.close()

    id_registro_edicao = None

    limpar_campos()
    carregar_lancamentos()
    gerar_relatorio()

    label_status.config(text="Alteração salva com sucesso.", fg="#2e7d32")

    messagebox.showinfo("Sucesso", "Registro alterado com sucesso!")


def limpar_campos():
    global id_registro_edicao

    id_registro_edicao = None

    entrada_descricao.delete(0, tk.END)
    entrada_categoria.delete(0, tk.END)
    entrada_valor.delete(0, tk.END)

    colocar_placeholder(entrada_descricao, "Ex: Venda de hambúrguer")
    colocar_placeholder(entrada_categoria, "Ex: Vendas, Ingredientes, Bebidas")
    colocar_placeholder(entrada_valor, "Ex: 50,00")

    label_status.config(text="Campos livres para novo cadastro.", fg="#455a64")


def carregar_lancamentos():
    for item in tabela.get_children():
        tabela.delete(item)

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id, tipo, descricao, categoria, valor, data
        FROM lancamentos
        ORDER BY id DESC
    """)

    registros = cursor.fetchall()
    conexao.close()

    for registro in registros:
        id_lancamento, tipo, descricao, categoria, valor, data = registro
        tabela.insert("", tk.END, iid=id_lancamento, values=(
            tipo,
            descricao,
            categoria,
            f"R$ {valor:.2f}",
            data
        ))


def calcular_totais():
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("SELECT SUM(valor) FROM lancamentos WHERE tipo = 'Receita'")
    total_receitas = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(valor) FROM lancamentos WHERE tipo = 'Despesa'")
    total_despesas = cursor.fetchone()[0] or 0

    saldo = total_receitas - total_despesas

    conexao.close()

    return total_receitas, total_despesas, saldo


def gerar_relatorio():
    total_receitas, total_despesas, saldo = calcular_totais()

    label_receitas_valor.config(text=f"R$ {total_receitas:.2f}")
    label_despesas_valor.config(text=f"R$ {total_despesas:.2f}")
    label_saldo_valor.config(text=f"R$ {saldo:.2f}")


def exportar_relatorio():
    total_receitas, total_despesas, saldo = calcular_totais()

    caminho_arquivo = filedialog.asksaveasfilename(
        title="Salvar Relatório Financeiro",
        defaultextension=".txt",
        filetypes=[("Arquivo de Texto", "*.txt")],
        initialfile="relatorio_colina_burguers.txt"
    )

    if not caminho_arquivo:
        return

    data_emissao = datetime.now().strftime("%d/%m/%Y %H:%M")

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT tipo, descricao, categoria, valor, data
        FROM lancamentos
        ORDER BY id DESC
    """)

    registros = cursor.fetchall()
    conexao.close()

    with open(caminho_arquivo, "w", encoding="utf-8") as arquivo:
        arquivo.write("RELATÓRIO FINANCEIRO - Colina Burguers\n")
        arquivo.write("Lanchonete localizada em Colina de Laranjeiras - Serra/ES\n")
        arquivo.write("=" * 60 + "\n\n")
        arquivo.write(f"Data de emissão: {data_emissao}\n\n")
        arquivo.write(f"Total de Receitas: R$ {total_receitas:.2f}\n")
        arquivo.write(f"Total de Despesas: R$ {total_despesas:.2f}\n")
        arquivo.write(f"Saldo Atual: R$ {saldo:.2f}\n\n")
        arquivo.write("LANÇAMENTOS REGISTRADOS\n")
        arquivo.write("-" * 60 + "\n")

        for registro in registros:
            tipo, descricao, categoria, valor, data = registro
            arquivo.write(
                f"{data} | {tipo} | {descricao} | {categoria} | R$ {valor:.2f}\n"
            )

    messagebox.showinfo(
        "Relatório Exportado",
        f"Relatório salvo com sucesso!\n\n{caminho_arquivo}"
    )


def visualizar_relatorio():

    total_receitas, total_despesas, saldo = calcular_totais()

    categorias = ["Receitas", "Despesas"]
    valores = [total_receitas, total_despesas]

    plt.figure(figsize=(8, 5))

    barras = plt.bar(
        categorias,
        valores,
        color=["#2e7d32", "#c62828"]
    )

    plt.title(
        "Relatório Financeiro - Colina Burguers",
        fontsize=14,
        fontweight="bold"
    )

    plt.ylabel("Valor (R$)")

    for barra in barras:

        altura = barra.get_height()

        plt.text(
            barra.get_x() + barra.get_width() / 2,
            altura,
            f"R$ {altura:.2f}",
            ha="center",
            va="bottom",
            fontweight="bold"
        )

    plt.figtext(
        0.5,
        0.02,
        f"Saldo Atual: R$ {saldo:.2f}",
        ha="center",
        fontsize=12,
        fontweight="bold"
    )

    plt.grid(axis="y", linestyle="--", alpha=0.3)

    plt.tight_layout()

    plt.show()


def excluir_registro():
    global id_registro_edicao

    selecionado = tabela.selection()

    if not selecionado:
        messagebox.showwarning("Atenção", "Selecione um registro na tabela para excluir.")
        return

    resposta = messagebox.askyesno(
        "Confirmar Exclusão",
        "Deseja realmente excluir o registro selecionado?"
    )

    if not resposta:
        return

    id_lancamento = selecionado[0]

    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM lancamentos WHERE id = ?", (id_lancamento,))
    conexao.commit()
    conexao.close()

    id_registro_edicao = None

    limpar_campos()
    carregar_lancamentos()
    gerar_relatorio()

    messagebox.showinfo("Sucesso", "Registro excluído com sucesso!")


def limpar_todos_registros():
    global id_registro_edicao

    resposta = messagebox.askyesno(
        "Confirmar Exclusão",
        "Tem certeza que deseja apagar TODOS os registros?\n\nEssa ação não poderá ser desfeita."
    )

    if not resposta:
        return

    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM lancamentos")
    conexao.commit()
    conexao.close()

    id_registro_edicao = None

    limpar_campos()
    carregar_lancamentos()
    gerar_relatorio()

    messagebox.showinfo("Sucesso", "Todos os registros foram removidos.")


def colocar_placeholder(campo, texto):
    campo.insert(0, texto)
    campo.config(fg="gray")


def remover_placeholder(event, campo, texto):
    if campo.get() == texto:
        campo.delete(0, tk.END)
        campo.config(fg="black")


def voltar_placeholder(event, campo, texto):
    if campo.get() == "":
        campo.insert(0, texto)
        campo.config(fg="gray")


def sair_tela_cheia(event=None):
    janela.attributes("-fullscreen", False)


criar_tabela()

janela = tk.Tk()
janela.title("Sistema Financeiro - Colina Burguers")
janela.attributes("-fullscreen", True)
janela.configure(bg="#eef1f5")
janela.bind("<Escape>", sair_tela_cheia)


style = ttk.Style()
style.theme_use("default")
style.configure(
    "Treeview",
    font=("Arial", 10),
    rowheight=28,
    background="white",
    fieldbackground="white"
)
style.configure(
    "Treeview.Heading",
    font=("Arial", 10, "bold")
)


frame_topo = tk.Frame(janela, bg="#1f2d36", height=95)
frame_topo.pack(fill="x")

titulo = tk.Label(
    frame_topo,
    text="SISTEMA DE CONTROLE FINANCEIRO - Colina Burguers",
    bg="#1f2d36",
    fg="white",
    font=("Arial", 24, "bold")
)
titulo.pack(pady=18)

subtitulo = tk.Label(
    frame_topo,
    text="Lanchonete localizada em Colina de Laranjeiras - Serra/ES | Controle de receitas, despesas e saldo financeiro",
    bg="#1f2d36",
    fg="#dfe6e9",
    font=("Arial", 12)
)
subtitulo.pack()


container = tk.Frame(janela, bg="#eef1f5")
container.pack(fill="both", expand=True, padx=35, pady=25)

area_superior = tk.Frame(container, bg="#eef1f5")
area_superior.pack(fill="x")


frame_form = tk.LabelFrame(
    area_superior,
    text=" Cadastro de Receita e Despesa ",
    bg="#eef1f5",
    fg="#1f2d36",
    font=("Arial", 13, "bold"),
    padx=25,
    pady=20
)
frame_form.pack(side="left", fill="both", expand=True, padx=(0, 18))


tk.Label(frame_form, text="Descrição:", bg="#eef1f5", font=("Arial", 11, "bold")).pack(anchor="w")
entrada_descricao = tk.Entry(frame_form, font=("Arial", 12))
entrada_descricao.pack(fill="x", pady=(5, 15), ipady=8)

tk.Label(frame_form, text="Categoria:", bg="#eef1f5", font=("Arial", 11, "bold")).pack(anchor="w")
entrada_categoria = tk.Entry(frame_form, font=("Arial", 12))
entrada_categoria.pack(fill="x", pady=(5, 15), ipady=8)

tk.Label(frame_form, text="Valor:", bg="#eef1f5", font=("Arial", 11, "bold")).pack(anchor="w")
entrada_valor = tk.Entry(frame_form, font=("Arial", 12))
entrada_valor.pack(fill="x", pady=(5, 18), ipady=8)

colocar_placeholder(entrada_descricao, "Ex: Venda de hambúrguer")
colocar_placeholder(entrada_categoria, "Ex: Vendas, Ingredientes, Bebidas")
colocar_placeholder(entrada_valor, "Ex: 50,00")

entrada_descricao.bind("<FocusIn>", lambda event: remover_placeholder(event, entrada_descricao, "Ex: Venda de hambúrguer"))
entrada_descricao.bind("<FocusOut>", lambda event: voltar_placeholder(event, entrada_descricao, "Ex: Venda de hambúrguer"))

entrada_categoria.bind("<FocusIn>", lambda event: remover_placeholder(event, entrada_categoria, "Ex: Vendas, Ingredientes, Bebidas"))
entrada_categoria.bind("<FocusOut>", lambda event: voltar_placeholder(event, entrada_categoria, "Ex: Vendas, Ingredientes, Bebidas"))

entrada_valor.bind("<FocusIn>", lambda event: remover_placeholder(event, entrada_valor, "Ex: 50,00"))
entrada_valor.bind("<FocusOut>", lambda event: voltar_placeholder(event, entrada_valor, "Ex: 50,00"))


label_status = tk.Label(
    frame_form,
    text="Campos livres para novo cadastro.",
    bg="#eef1f5",
    fg="#455a64",
    font=("Arial", 10, "bold")
)
label_status.pack(anchor="w", pady=(0, 8))


area_botoes = tk.Frame(frame_form, bg="#eef1f5")
area_botoes.pack(fill="x", pady=5)

tk.Button(
    area_botoes,
    text="Registrar Receita",
    bg="#2e7d32",
    fg="white",
    font=("Arial", 12, "bold"),
    height=2,
    command=lambda: salvar_lancamento("Receita")
).pack(side="left", fill="x", expand=True, padx=(0, 8))

tk.Button(
    area_botoes,
    text="Registrar Despesa",
    bg="#c62828",
    fg="white",
    font=("Arial", 12, "bold"),
    height=2,
    command=lambda: salvar_lancamento("Despesa")
).pack(side="left", fill="x", expand=True, padx=8)

tk.Button(
    area_botoes,
    text="Limpar Campos",
    bg="#455a64",
    fg="white",
    font=("Arial", 12, "bold"),
    height=2,
    command=limpar_campos
).pack(side="left", fill="x", expand=True, padx=(8, 0))


frame_resumo = tk.LabelFrame(
    area_superior,
    text=" Resumo Financeiro ",
    bg="#eef1f5",
    fg="#1f2d36",
    font=("Arial", 13, "bold"),
    padx=20,
    pady=20,
    width=420
)
frame_resumo.pack(side="right", fill="both")
frame_resumo.pack_propagate(False)


def criar_card(pai, titulo_card, cor):
    card = tk.Frame(pai, bg=cor, height=90)
    card.pack(fill="x", pady=8)
    card.pack_propagate(False)

    tk.Label(
        card,
        text=titulo_card,
        bg=cor,
        fg="white",
        font=("Arial", 12, "bold")
    ).pack(pady=(12, 2))

    label_valor = tk.Label(
        card,
        text="R$ 0.00",
        bg=cor,
        fg="white",
        font=("Arial", 20, "bold")
    )
    label_valor.pack()

    return label_valor


label_receitas_valor = criar_card(frame_resumo, "TOTAL DE RECEITAS", "#2e7d32")
label_despesas_valor = criar_card(frame_resumo, "TOTAL DE DESPESAS", "#c62828")
label_saldo_valor = criar_card(frame_resumo, "SALDO ATUAL", "#1565c0")


frame_lista = tk.LabelFrame(
    container,
    text=" Lançamentos Registrados ",
    bg="#eef1f5",
    fg="#1f2d36",
    font=("Arial", 13, "bold"),
    padx=15,
    pady=15
)
frame_lista.pack(fill="both", expand=True, pady=(22, 8))

colunas = ("Tipo", "Descrição", "Categoria", "Valor", "Data")
tabela = ttk.Treeview(frame_lista, columns=colunas, show="headings")

for coluna in colunas:
    tabela.heading(coluna, text=coluna)

tabela.column("Tipo", width=120, anchor="center")
tabela.column("Descrição", width=350, anchor="center")
tabela.column("Categoria", width=250, anchor="center")
tabela.column("Valor", width=160, anchor="center")
tabela.column("Data", width=180, anchor="center")

barra_rolagem = ttk.Scrollbar(frame_lista, orient="vertical", command=tabela.yview)
tabela.configure(yscrollcommand=barra_rolagem.set)

tabela.pack(side="left", fill="both", expand=True)
barra_rolagem.pack(side="right", fill="y")


frame_acoes = tk.Frame(frame_form, bg="#eef1f5")
frame_acoes.pack(fill="x", pady=(10, 0))

tk.Button(
    frame_acoes,
    text="📄 Exportar Relatório",
    bg="#1565c0",
    fg="white",
    font=("Arial", 10, "bold"),
    command=exportar_relatorio
).grid(row=0, column=0, padx=4, pady=4, sticky="ew")

tk.Button(
    frame_acoes,
    text="📈 Visualizar Relatório",
    bg="#1976d2",
    fg="white",
    font=("Arial", 10, "bold"),
    command=visualizar_relatorio
).grid(row=0, column=1, padx=4, pady=4, sticky="ew")

tk.Button(
    frame_acoes,
    text="✏ Editar Registro",
    bg="#6a1b9a",
    fg="white",
    font=("Arial", 10, "bold"),
    command=carregar_para_edicao
).grid(row=0, column=2, padx=4, pady=4, sticky="ew")

tk.Button(
    frame_acoes,
    text="💾 Salvar Alteração",
    bg="#00897b",
    fg="white",
    font=("Arial", 10, "bold"),
    command=salvar_alteracao
).grid(row=0, column=3, padx=4, pady=4, sticky="ew")

tk.Button(
    frame_acoes,
    text="❌ Excluir Registro",
    bg="#e67e22",
    fg="white",
    font=("Arial", 10, "bold"),
    command=excluir_registro
).grid(row=0, column=4, padx=4, pady=4, sticky="ew")

tk.Button(
    frame_acoes,
    text="🗑 Limpar Todos",
    bg="#b71c1c",
    fg="white",
    font=("Arial", 10, "bold"),
    command=limpar_todos_registros
).grid(row=0, column=5, padx=4, pady=4, sticky="ew")

for i in range(6):
    frame_acoes.grid_columnconfigure(i, weight=1)


rodape = tk.Label(
    janela,
    text="Projeto aplicado na lanchonete Colina Burguers | Python, Tkinter e SQLite | Pressione ESC para sair da tela cheia",
    bg="#1f2d36",
    fg="white",
    font=("Arial", 10)
)
rodape.pack(fill="x", ipady=8)


carregar_lancamentos()
gerar_relatorio()

janela.mainloop()