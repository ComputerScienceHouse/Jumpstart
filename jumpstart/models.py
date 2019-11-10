from jumpstart import db

class File(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(80), nullable=False)

	def __repr__(self):
		return f"{self.title}"

class Ann(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(200), nullable=False)

	def __repr__(self):
		return f"{self.title}"