# models.py

from extensions import db

class EnGrade1(db.Model):
    __tablename__ = 'en_grade1'
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(50), nullable=False, unique=True)
    bin = db.Column(db.LargeBinary, nullable=False)  # Assuming 'bin' stores binary data for braille

    def __repr__(self):
        return f"<EnGrade1 id={self.id} word='{self.word}'>"
