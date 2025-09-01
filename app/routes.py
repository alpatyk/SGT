from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import login_user, current_user, logout_user, login_required
from app import db, bcrypt
from app.models import User, Task
from app.forms import RegistrationForm, LoginForm, TaskForm

main = Blueprint('main', __name__)

@main.route("/")
@main.route("/dashboard")
@login_required
def dashboard():
    # Tarefas criadas pelo usuário
    my_tasks = Task.query.filter_by(user_id=current_user.id).all()
    
    # Tarefas atribuídas ao usuário
    assigned_tasks = Task.query.filter_by(assigned_to=current_user.id).all()
    
    # Todas as tarefas (para admin ou visualização de grupo)
    all_tasks = Task.query.all()
    
    # Filtrar por status se solicitado
    status_filter = request.args.get('status')
    if status_filter and status_filter != 'todos':
        my_tasks = [task for task in my_tasks if task.status == status_filter]
        assigned_tasks = [task for task in assigned_tasks if task.status == status_filter]
    
    return render_template('dashboard.html', 
                        my_tasks=my_tasks, 
                        assigned_tasks=assigned_tasks,
                        all_tasks=all_tasks)

@main.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Sua conta foi criada! Você já pode fazer login.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)

@main.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Login não realizado. Verifique email e senha.', 'danger')
    return render_template('login.html', title='Login', form=form)

@main.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main.route("/task/new", methods=['GET', 'POST'])
@login_required
def new_task():
    form = TaskForm()
    
    users = User.query.all()
    form.assigned_to.choices = [(0, 'Ninguém')] + [(user.id, user.username) for user in users]
    
    if form.validate_on_submit():
        assigned_to = form.assigned_to.data if form.assigned_to.data != 0 else None
        task = Task(
            title=form.title.data, 
            description=form.description.data,
            status=form.status.data,
            user_id=current_user.id,
            assigned_to=assigned_to
        )
        db.session.add(task)
        db.session.commit()
        flash('Tarefa criada com sucesso!', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('create_task.html', title='Nova Tarefa', form=form, legend='Nova Tarefa')

@main.route("/task/<int:task_id>")
@login_required
def task(task_id):
    task = Task.query.get_or_404(task_id)
    return render_template('task.html', title=task.title, task=task)

@main.route("/task/<int:task_id>/update", methods=['GET', 'POST'])
@login_required
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('Você não tem permissão para editar esta tarefa.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    form = TaskForm()
    
    users = User.query.all()
    form.assigned_to.choices = [(0, 'Ninguém')] + [(user.id, user.username) for user in users]
    
    if form.validate_on_submit():
        assigned_to = form.assigned_to.data if form.assigned_to.data != 0 else None
        task.title = form.title.data
        task.description = form.description.data
        task.status = form.status.data
        task.assigned_to = assigned_to
        db.session.commit()
        flash('Tarefa atualizada com sucesso!', 'success')
        return redirect(url_for('main.task', task_id=task.id))
    elif request.method == 'GET':
        form.title.data = task.title
        form.description.data = task.description
        form.status.data = task.status
        form.assigned_to.data = task.assigned_to if task.assigned_to else 0
    
    return render_template('create_task.html', title='Editar Tarefa', form=form, legend='Editar Tarefa')

@main.route("/task/<int:task_id>/delete", methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('Você não tem permissão para excluir esta tarefa.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    db.session.delete(task)
    db.session.commit()
    flash('Tarefa excluída com sucesso!', 'success')
    return redirect(url_for('main.dashboard'))