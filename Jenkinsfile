// Jenkinsfile — TienditaMarian (monorepo backend Django/DRF + frontend React/Vite)
//
// Espeja el flujo de .github/workflows/ci.yml para quien orqueste el pipeline
// en Jenkins (on-prem / infra propia). Los stages siguen el orden rápido -> lento:
// lint -> tests -> deploy check -> frontend build -> (opcional) imagen Docker.
//
// Requisitos del agente: Docker disponible (se usan imágenes efímeras por stage,
// así el controlador de Jenkins no necesita Python ni Node instalados).

pipeline {
    // 'agent any' + docker.image(...).inside {} por stage: cada herramienta corre
    // en su propia imagen y no ensucia el nodo. Alternativa: un agente Kubernetes
    // o un contenedor global con 'agent { docker { image '...' } }'.
    agent any

    options {
        timestamps()
        // Un build colgado no debe bloquear la cola indefinidamente.
        timeout(time: 30, unit: 'MINUTES')
    }

    environment {
        // config.settings.test inyecta sus propios defaults (SQLite en memoria),
        // así que el backend rápido corre sin .env ni secretos.
        DJANGO_SETTINGS_MODULE = 'config.settings.test'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        // -------------------------------------------------------------------
        // Backend: lint (ruff) — el paso más barato, descarta fallos de estilo
        // antes de gastar minutos en tests.
        // -------------------------------------------------------------------
        stage('Backend Lint') {
            agent {
                docker { image 'python:3.12-slim'; reuseNode true }
            }
            steps {
                dir('backend') {
                    sh 'python -m pip install --upgrade pip'
                    sh 'pip install -r requirements/dev.txt'
                    sh 'ruff check .'
                }
            }
        }

        // -------------------------------------------------------------------
        // Backend: tests + cobertura contra SQLite.
        // Para el test de concurrencia real (select_for_update, que SQLite
        // ignora) hay que levantar Postgres. En Jenkins se hace con un sidecar:
        //
        //   docker.image('postgres:16-alpine').withRun(
        //       '-e POSTGRES_USER=tiendita -e POSTGRES_PASSWORD=tiendita ' +
        //       '-e POSTGRES_DB=tiendita_test') { c ->
        //       docker.image('python:3.12-slim').inside("--link ${c.id}:db") {
        //           dir('backend') {
        //               withEnv(['DATABASE_URL=postgres://tiendita:tiendita@db:5432/tiendita_test']) {
        //                   sh 'pip install -r requirements/dev.txt'
        //                   sh 'pytest -rs'   // -rs hace visibles los skips
        //               }
        //           }
        //       }
        //   }
        // -------------------------------------------------------------------
        stage('Backend Tests') {
            agent {
                docker { image 'python:3.12-slim'; reuseNode true }
            }
            steps {
                dir('backend') {
                    sh 'python -m pip install --upgrade pip'
                    sh 'pip install -r requirements/dev.txt'
                    // Cobertura como condición de fallo, no métrica decorativa.
                    // 90 frente a una cobertura real del 91,8 %: el 70 anterior
                    // dejaba margen para borrar un tercio de la suite sin ruido.
                    sh 'pytest --cov --cov-report=term-missing --cov-fail-under=90'
                }
            }
        }

        // -------------------------------------------------------------------
        // Backend: hardening de producción (check --deploy). Valida SSL,
        // HSTS, cookies secure y fortaleza de SECRET_KEY con la config prod.
        // -------------------------------------------------------------------
        stage('Backend Deploy Check') {
            agent {
                docker { image 'python:3.12-slim'; reuseNode true }
            }
            environment {
                DJANGO_SETTINGS_MODULE = 'config.settings.prod'
                ALLOWED_HOSTS          = 'tienditademarian.com'
                DATABASE_URL           = 'sqlite:///db.sqlite3'
                SECURE_HTTPS           = 'True'
            }
            steps {
                dir('backend') {
                    sh 'python -m pip install --upgrade pip'
                    sh 'pip install -r requirements/prod.txt'
                    // Clave efímera solo para el check: no sirve tráfico ni se guarda.
                    sh '''
                        export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(64))')"
                        python manage.py check --deploy --fail-level WARNING
                    '''
                }
            }
        }

        // -------------------------------------------------------------------
        // Frontend: lint + tests + build. `npm run build` verifica que el
        // frontend CONSTRUYE, no solo que lintea.
        // -------------------------------------------------------------------
        stage('Frontend Build+Test') {
            agent {
                docker { image 'node:24-slim'; reuseNode true }
            }
            steps {
                dir('frontend') {
                    sh 'npm ci'          // instala exactamente lo del lockfile
                    sh 'npm run lint'
                    sh 'npm test'
                    sh 'npm run build'
                }
            }
        }

        // -------------------------------------------------------------------
        // Opcional: construir (y publicar) la imagen Docker del backend.
        // Solo en la rama principal para no empujar imágenes desde cada PR.
        // Las credenciales del registry van por el store de Jenkins, nunca en
        // claro: withCredentials + credentials('id') resuelve usuario/token.
        // -------------------------------------------------------------------
        stage('Docker Build') {
            when { branch 'main' }
            steps {
                dir('backend') {
                    script {
                        def img = docker.build("tiendita-backend:${env.BUILD_NUMBER}")
                        // Publicación (descomentar cuando haya registry configurado):
                        // docker.withRegistry('https://registry.example.com',
                        //                     'registry-credentials-id') {
                        //     img.push()
                        //     img.push('latest')
                        // }
                    }
                }
            }
        }
    }

    post {
        always {
            // Limpia el workspace para no arrastrar artefactos entre builds.
            cleanWs()
        }
    }
}
