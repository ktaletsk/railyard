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
                    sh 'pip install --user .'
                    sh 'railyard assemble stacks/base.yaml stacks/R.yaml stacks/java.yaml temp'
                    sh 'ls -la temp'
                }
            }
        }
    }
}