pipeline {
    agent { 
        docker { 
            image 'python:3.7' 
            args '--network=host'    
        } 
    }
    stages {
        stage('build') {
            steps {
                withEnv(["HOME=${env.WORKSPACE}"]) {
                    sh 'python --version'
                    sh 'ls -la'
                    sh 'pip install --user -r requirements.txt'
                }
            }
        }
    }
}