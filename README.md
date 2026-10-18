# SoftQuest

Proyecto desarrollado por el equipo **Los Guerreros Z** para la materia TSP.

## Requisitos

- Python 3 instalado.
- Una terminal ubicada en la raíz del proyecto.

## Instalación

### 1. Crear el entorno virtual

```bash
python -m venv venv
```

### 2. Activar el entorno virtual

**Windows (PowerShell):**

```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**

```bat
venv\Scripts\activate.bat
```

**macOS/Linux:**

```bash
source venv/bin/activate
```

### 3. Instalar las dependencias

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Autenticación

La aplicación usa la autenticación integrada de Django. Antes del primer inicio,
aplica las migraciones:

```bash
python manage.py migrate
```

Las personas pueden crear su cuenta en `/registro/` e iniciar sesión en `/login/`
con su nombre de usuario o correo electrónico. Cada cuenta se vincula a un perfil
`login.Usuario`; los registros de progreso en `contenido` apuntan a ese perfil.

---
