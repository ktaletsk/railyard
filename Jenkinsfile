pipeline {
    agent {
        label 'master'
    }
    stages {
        stage('assemble') {
            agent { 
                docker { 
                    image 'python:3.7' 
                    args '--network=host'
                    reuseNode true   
                } 
            }
            steps {
                checkout scm
                withEnv(["HOME=${env.WORKSPACE}"]) {
                    sh 'echo $HOME'
                    sh 'echo $PATH'
                    sh "pip install -r requirements.txt --user"
                    sh 'pip install . --user'
                    sh '$HOME/.local/bin/railyard assemble stacks/base.yaml stacks/R.yaml stacks/java.yaml temp'
                    sh 'ls -la temp'
                    sh 'cat temp/Dockerfile'
                }
            }
        }
        stage('build') {
            steps {
                script {
                    dir('temp') {
                        sh 'ls -la'
                        docker.withRegistry('https://registry-1.docker.io/v2/', 'dockerhub') {
                            def image = docker.build('ktaletsk/polus-notebook:jenkins-test', '--network=host --no-cache ./')
                            image.push()
                        }
                    }
                }
            }
        }
    }
}