import os
from flask import Flask, render_template, request, redirect, url_for, flash
from config import Config
from models import db, Product, Purchase
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config.from_object(Config)
app.config['UPLOAD_FOLDER'] = 'static/images/'
db.init_app(app)

with app.app_context():
    db.create_all()

# Route to display products
@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

# Route to view product details and buy
@app.route('/product/<int:product_id>', methods=['GET', 'POST'])
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        purchase = Purchase(product_id=product_id)
        db.session.add(purchase)
        db.session.commit()
        flash("Purchase successful!", "success")
        return redirect(url_for('index'))
    return render_template('product.html', product=product)

# Route to add new products (admin page)
@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        detail = request.form['detail']
        
        # Handle image upload
        image_file = request.files['image']
        if image_file:
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
            new_product = Product(name=name, detail=detail, image=filename)
            db.session.add(new_product)
            db.session.commit()
            flash("Product added successfully!", "success")
            return redirect(url_for('index'))
    return render_template('add_product.html')

if __name__ == '__main__':
    app.run(debug=True)
