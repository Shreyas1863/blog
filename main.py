from flask import Flask,render_template,redirect,url_for,flash
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column,relationship
from sqlalchemy import Integer,String,Text
from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField,PasswordField
from wtforms.validators import DataRequired,Email,URL
from flask_ckeditor import CKEditor,CKEditorField
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import UserMixin,login_user,LoginManager,login_required,current_user,logout_user
from flask_gravatar import Gravatar

flask_object=Flask(__name__)
flask_object.config['SECRET_KEY']='8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
bootstrap_object=Bootstrap5(flask_object)
ckeditor_object=CKEditor(flask_object)
login_manager_object=LoginManager()

class Base(DeclarativeBase):
    pass

flask_object.config['SQLALCHEMY_DATABASE_URI']='sqlite:///posts.db'
db=SQLAlchemy(model_class=Base)
db.init_app(flask_object)
login_manager_object.init_app(flask_object)

class User(UserMixin,db.Model):
    __tablename__="users"
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    email:Mapped[str]=mapped_column(String(100),unique=True)
    password:Mapped[str]=mapped_column(String(100))
    name:Mapped[str]=mapped_column(String(1000))

    posts=relationship("BlogPost",back_populates="author")
    comments=relationship("Comment",back_populates="comment_author")

class BlogPost(db.Model):
    __tablename__="blog_posts"
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    title:Mapped[str]=mapped_column(String(250),unique=True,nullable=False)
    subtitle:Mapped[str]=mapped_column(String(250),nullable=False)
    date:Mapped[str]=mapped_column(String(250),nullable=False)
    body:Mapped[str]=mapped_column(Text,nullable=False)
    img_url:Mapped[str]=mapped_column(String(250),nullable=False)

    author_id:Mapped[int]=mapped_column(Integer,db.ForeignKey("users.id"))
    author=relationship("User",back_populates="posts")

    comments=relationship("Comment",back_populates="parent_post")

class Comment(db.Model):
    __tablename__="comments"
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    body:Mapped[str]=mapped_column(Text, nullable=False)

    author_id:Mapped[int]=mapped_column(Integer,db.ForeignKey("users.id"))
    comment_author=relationship("User",back_populates="comments")

    post_id:Mapped[str]=mapped_column(Integer,db.ForeignKey("blog_posts.id"))
    parent_post=relationship("BlogPost",back_populates="comments")

class BlogForm(FlaskForm):
    title_string_field_object=StringField('Blog Post Title',validators=[DataRequired()])
    subtitle_string_field_object=StringField('Subtitle',validators=[DataRequired()])
    body_ckeditor_field_object=CKEditorField('Blog Content',validators=[DataRequired()])
    author_string_field_object=StringField('Your Name',validators=[DataRequired()])
    image_url_string_field_object=StringField('Blog Image URL',validators=[DataRequired(),URL()])
    submit_button_submit_field_object=SubmitField('Submit Blog')

class RegisterForm(FlaskForm):
    name_string_field_object=StringField('Name',validators=[DataRequired()])
    email_string_field_object=StringField('Email',validators=[DataRequired(),Email()])
    password_password_field_object=PasswordField('Password',validators=[DataRequired()])
    submit_button_submit_field_object=SubmitField('Register')

class LoginForm(FlaskForm):
    email_string_field_object=StringField('Email',validators=[DataRequired(),Email()])
    password_password_field_object=PasswordField('Password',validators=[DataRequired()])
    submit_button_submit_field_object=SubmitField('Login')

class CommentForm(FlaskForm):
    body_ckeditor_field_object=CKEditorField('Comment',validators=[DataRequired()])
    submit_button_submit_field_object=SubmitField('Submit Comment')

gravatar_object=Gravatar(flask_object,size=50,rating='g',default='retro',force_default=False,force_lower=False,use_ssl=False,base_url=None)

@login_manager_object.user_loader
def load_user(user_id):
    return db.get_or_404(User,user_id)

@flask_object.route('/')
def home():
    result=db.session.execute(db.select(BlogPost).order_by(BlogPost.id))
    blog_post_list=result.scalars().all()
    return render_template("index.html",blog_post_list=blog_post_list,logged_in=current_user.is_authenticated,current_user=current_user)

@flask_object.route("/<int:num>",methods=["GET","POST"])
def blog(num):
    comment_form_object=CommentForm()
    result=db.session.execute(db.select(BlogPost).where(BlogPost.id==num))
    blog_post=result.scalars().all()
    if comment_form_object.validate_on_submit()==1:
        if current_user.is_authenticated:
            db.session.add(Comment(body=comment_form_object.body_ckeditor_field_object.data,
                                   comment_author=current_user,
                                   parent_post=blog_post[0]
                                   )
                           )
            db.session.commit()
            return render_template("blog.html",title=blog_post[0].title,subtitle=blog_post[0].subtitle,body=blog_post[0].body,author=blog_post[0].author,num=num,current_user=current_user,comment_form_object=comment_form_object,parent_post=blog_post[0])
        else:
            return redirect(url_for('login'))
    else:
        return render_template("blog.html",title=blog_post[0].title,subtitle=blog_post[0].subtitle,body=blog_post[0].body,author=blog_post[0].author,num=num,current_user=current_user,comment_form_object=comment_form_object,parent_post=blog_post[0])

@flask_object.route("/make",methods=["GET","POST"])
@login_required
def make():
    if current_user.id==1:
        blog_form_object=BlogForm()
        validate=blog_form_object.validate_on_submit()
        if validate==1:# 1=POST,0=GET
            db.session.add(BlogPost(title=blog_form_object.title_string_field_object.data,
                                    date="March 07, 2026",
                                    body=blog_form_object.body_ckeditor_field_object.data,
                                    author=current_user,
                                    img_url=blog_form_object.image_url_string_field_object.data,
                                    subtitle=blog_form_object.subtitle_string_field_object.data
                                    )
                           )
            db.session.commit()
            return redirect(url_for('home'))
        else:
            return render_template("make-post.html",blog_form_object=blog_form_object)
    else:
        return redirect(url_for('home'))

@flask_object.route('/edit/<int:num>',methods=["GET","POST"])
@login_required
def edit(num):
    if current_user.id==1:
        result=db.session.execute(db.select(BlogPost).where(BlogPost.id==num))
        blog_post=result.scalars().all()
        edit_form_object=BlogForm(title_string_field_object=blog_post[0].title,subtitle_string_field_object=blog_post[0].subtitle,body_ckeditor_field_object=blog_post[0].body,author_string_field_object=blog_post[0].author.name,image_url_string_field_object=blog_post[0].img_url)
        if edit_form_object.validate_on_submit()==1:# 1=POST,0=GET
            edit_blog=db.session.execute(db.select(BlogPost).where(BlogPost.id==num)).scalar()
            edit_blog.title=edit_form_object.title_string_field_object.data
            edit_blog.subtitle=edit_form_object.subtitle_string_field_object.data
            edit_blog.body=edit_form_object.body_ckeditor_field_object.data
            edit_blog.author=current_user
            edit_blog.img_url=edit_form_object.image_url_string_field_object.data
            db.session.commit()
            return redirect(url_for('home'))
        else:
            return render_template("edit.html",edit_form_object=edit_form_object)
    else:
        return redirect(url_for('home'))

@flask_object.route('/delete/<int:num>')
@login_required
def delete(num):
    if current_user.id==1:
        blog=db.session.execute(db.select(BlogPost).where(BlogPost.id==num)).scalar()
        db.session.delete(blog)
        db.session.commit()
        return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))

@flask_object.route('/register',methods=["GET","POST"])
def register():
    register_user_object=RegisterForm()
    if register_user_object.validate_on_submit()==1:
        login_user_element=db.session.execute(db.select(User).where(User.email == register_user_object.email_string_field_object.data)).scalar()
        if login_user_element:
            flash("Already signed up, log in instead!")
            return redirect(url_for('login'))
        else:
            hash_and_salted_password=generate_password_hash(register_user_object.password_password_field_object.data,method='pbkdf2:sha256',salt_length=8)
            new_user=User(email=register_user_object.email_string_field_object.data,
                          password=hash_and_salted_password,
                          name=register_user_object.name_string_field_object.data)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('home'))
    else:
        return render_template("register.html",user_object=register_user_object)

@flask_object.route('/login',methods=["GET","POST"])
def login():
    login_user_object=LoginForm()
    if login_user_object.validate_on_submit()==1:
        login_user_element=db.session.execute(db.select(User).where(User.email==login_user_object.email_string_field_object.data)).scalar()
        if check_password_hash(login_user_element.password,login_user_object.password_password_field_object.data):
            login_user(login_user_element)
            return redirect(url_for('home'))
        else:
            flash("Wrong Password")
            return render_template("login.html",user_object=login_user_object)
    else:
        return render_template("login.html",user_object=login_user_object)

@flask_object.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@flask_object.route("/about")
def about():
    return render_template("about.html")

@flask_object.route("/contact")
def contact():
    return render_template("contact.html")

if __name__ == "__main__":
    flask_object.run(debug=False)