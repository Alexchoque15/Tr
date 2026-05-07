import os
import tkinter as tk
from tkinter import ttk, messagebox
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# --- CONFIGURACIÓN BACKEND ---
app = Flask(__name__)
db_path = os.path.join(os.path.dirname(__file__), 'biblioteca_tablas.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELOS (SQLAlchemy) ---
libro_genero = db.Table('libro_genero',
    db.Column('libro_id', db.Integer, db.ForeignKey('libro.id'), primary_key=True),
    db.Column('genero_id', db.Integer, db.ForeignKey('genero.id'), primary_key=True)
)

class Autor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    nacionalidad = db.Column(db.String(50))
    libros = db.relationship('Libro', backref='autor', cascade="all, delete-orphan")

class Libro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    anio = db.Column(db.Integer)
    autor_id = db.Column(db.Integer, db.ForeignKey('autor.id'))
    generos = db.relationship('Genero', secondary=libro_genero, backref='libros')

class Genero(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True)

# --- INTERFAZ CON TABLAS ---
class AppBibliotecaTablas:
    def __init__(self, root):
        self.root = root
        self.root.title("SISTEMA DE GESTIÓN DE BIBLIOTECA")
        self.root.geometry("800x700")
        self.root.attributes('-topmost', True)
        self.root.configure(bg="#1e1e2e")

        # Estilos
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Treeview", background="#313244", foreground="white", fieldbackground="#313244", borderwidth=0)
        self.style.map("Treeview", background=[('selected', '#89b4fa')])
        self.style.configure("TNotebook", background="#1e1e2e", borderwidth=0)
        self.style.configure("TNotebook.Tab", padding=[10, 5], font=("Segoe UI", 10))

        # Pestañas
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Secciones
        self.tab_admin = tk.Frame(self.notebook, bg="#1e1e2e")
        self.tab_visualizar = tk.Frame(self.notebook, bg="#1e1e2e")
        
        self.notebook.add(self.tab_admin, text=" 📝 REGISTRO Y ACCIONES ")
        self.notebook.add(self.tab_visualizar, text=" 📊 VISUALIZAR TABLAS ")

        self.setup_tab_admin()
        self.setup_tab_visualizar()

    def setup_tab_admin(self):
        # Panel de botones arriba
        frame_btns = tk.Frame(self.tab_admin, bg="#1e1e2e")
        frame_btns.pack(fill="x", pady=20)

        tk.Button(frame_btns, text="INICIALIZAR DB", bg="#a6e3a1", command=self.init_db, font=("Arial", 9, "bold")).pack(side="left", padx=10)
        tk.Button(frame_btns, text="CARGAR DATOS SEMILLA", bg="#fab387", command=self.seed_data, font=("Arial", 9, "bold")).pack(side="left", padx=10)
        tk.Button(frame_btns, text="BORRAR PRIMER AUTOR (CASCADA)", bg="#f38ba8", command=self.delete_data, font=("Arial", 9, "bold")).pack(side="right", padx=10)

        # Formulario
        lbl_style = {"bg": "#1e1e2e", "fg": "#cdd6f4", "font": ("Arial", 10)}
        form = tk.LabelFrame(self.tab_admin, text=" Añadir Nuevo Registro ", bg="#1e1e2e", fg="#89b4fa", padx=20, pady=20)
        form.pack(fill="x", padx=10)

        tk.Label(form, text="Nombre Autor:", **lbl_style).grid(row=0, column=0, sticky="w")
        self.ent_autor = tk.Entry(form, width=30); self.ent_autor.grid(row=0, column=1, pady=5)

        tk.Label(form, text="Título Libro:", **lbl_style).grid(row=1, column=0, sticky="w")
        self.ent_libro = tk.Entry(form, width=30); self.ent_libro.grid(row=1, column=1, pady=5)

        tk.Button(form, text="GUARDAR EN DB", bg="#89b4fa", command=self.save_data).grid(row=2, columnspan=2, pady=10, sticky="e")

    def setup_tab_visualizar(self):
        # SUB-SECCIONES DENTRO DE VISUALIZAR
        tk.Label(self.tab_visualizar, text="CONTENIDO DE LA BASE DE DATOS", bg="#1e1e2e", fg="#89b4fa", font=("Arial", 12, "bold")).pack(pady=10)
        
        btn_refresh = tk.Button(self.tab_visualizar, text="🔄 ACTUALIZAR TODAS LAS TABLAS", command=self.refresh_tables, bg="#94e2d5")
        btn_refresh.pack(pady=5)

        # --- TABLA AUTORES ---
        tk.Label(self.tab_visualizar, text="Sección: Autores (Relación 1-N)", bg="#1e1e2e", fg="white").pack(anchor="w", padx=20)
        self.tree_autores = ttk.Treeview(self.tab_visualizar, columns=("ID", "Nombre", "Nacionalidad", "Libros"), show="headings", height=5)
        self.setup_tree(self.tree_autores, [("ID", 50), ("Nombre", 200), ("Nacionalidad", 150), ("Libros", 300)])

        # --- TABLA GÉNEROS ---
        tk.Label(self.tab_visualizar, text="Sección: Géneros (Relación N-M)", bg="#1e1e2e", fg="white").pack(anchor="w", padx=20, pady=(10,0))
        self.tree_generos = ttk.Treeview(self.tab_visualizar, columns=("ID", "Género", "Libros Asociados"), show="headings", height=5)
        self.setup_tree(self.tree_generos, [("ID", 50), ("Género", 150), ("Libros Asociados", 500)])

    def setup_tree(self, tree, columns):
        for col, width in columns:
            tree.heading(col, text=col)
            tree.column(col, width=width)
        tree.pack(fill="x", padx=20, pady=5)

    # --- LÓGICA ---
    def refresh_tables(self):
        # Limpiar
        for tree in [self.tree_autores, self.tree_generos]:
            for item in tree.get_children(): tree.delete(item)
        
        with app.app_context():
            # Cargar Autores
            for a in Autor.query.all():
                libros = ", ".join([l.titulo for l in a.libros])
                self.tree_autores.insert("", "end", values=(a.id, a.nombre, a.nacionalidad, libros))
            
            # Cargar Géneros
            for g in Genero.query.all():
                libros = ", ".join([l.titulo for l in g.libros])
                self.tree_generos.insert("", "end", values=(g.id, g.nombre, libros))

    def init_db(self):
        with app.app_context():
            db.create_all()
            messagebox.showinfo("DB", "Base de Datos Inicializada")

    def seed_data(self):
        with app.app_context():
            if not Autor.query.first():
                g1 = Genero(nombre="Ciencia"); g2 = Genero(nombre="Historia")
                a1 = Autor(nombre="Carl Sagan", nacionalidad="USA")
                l1 = Libro(titulo="Cosmos", anio=1980, autor=a1, generos=[g1, g2])
                db.session.add_all([g1, g2, a1, l1])
                db.session.commit()
                self.refresh_tables()
                messagebox.showinfo("Éxito", "Datos semilla cargados")

    def save_data(self):
        with app.app_context():
            nom, tit = self.ent_autor.get(), self.ent_libro.get()
            if nom and tit:
                a = Autor(nombre=nom); l = Libro(titulo=tit, autor=a)
                db.session.add(a); db.session.commit()
                self.ent_autor.delete(0, 'end'); self.ent_libro.delete(0, 'end')
                self.refresh_tables()

    def delete_data(self):
        with app.app_context():
            a = Autor.query.first()
            if a:
                db.session.delete(a); db.session.commit()
                self.refresh_tables()
                messagebox.showwarning("Cascada", f"Autor {a.nombre} y sus libros eliminados.")

if __name__ == "__main__":
    root = tk.Tk()
    mi_app = AppBibliotecaTablas(root)
    root.mainloop()