# models.py

from extensions import db

class EnGrade1(db.Model):
    __tablename__ = 'en_grade1'
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(50), nullable=False, unique=True)
    bin = db.Column(db.LargeBinary, nullable=False)  # Assuming 'bin' stores binary data for braille

    def __repr__(self):
        return f"<EnGrade1 id={self.id} word='{self.word}'>"

class DiaryEntry(db.Model):
    __tablename__ = 'diary'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    content = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<DiaryEntry id={self.id} - entry_date={self.entry_date}>"