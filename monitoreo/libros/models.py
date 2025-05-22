from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Libro(db.Model):
    __tablename__ = 'libros'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    genero_id = db.Column(db.Integer, nullable=False)
    genero = db.Column(db.String(100), nullable=False)
    autor_id = db.Column(db.Integer, nullable=False)
    autor = db.Column(db.String(100), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'titulo': self.titulo,
            'descripcion': self.descripcion,
            'genero_id': self.genero_id,
            'genero': self.genero,
            'autor_id': self.autor_id,
            'autor': self.autor
        }
