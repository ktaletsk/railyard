pipeline {
    agent {
        label 'master'
    }
    stages {
        stage('Checkout source code') {
            steps {
                cleanWs()
                checkout scm
            }
        }
        stage('Assemble') {
            agent { 
                docker { 
                    image 'python:3.7' 
                    args '--network=host'
                    reuseNode true   
                } 
            }
            steps {
                withEnv(["HOME=${env.WORKSPACE}"]) {
                    sh 'echo $HOME'
                    sh 'echo $PATH'
                    sh "pip install -r requirements.txt --user"
                    sh 'pip install . --user'
                    sh '$HOME/.local/bin/railyard assemble stacks/base.yaml stacks/R.yaml stacks/java.yaml manifests'
                    sh '$HOME/.local/bin/railyard assemble stacks/base.yaml stacks/Python-datascience.yaml stacks/Python-dataviz.yaml manifests'
                    sh 'ls -la manifests/*'
                }
            }
        }
        stage('Build') {
            steps {
                script {
                    dir('manifests') {
                        def containerVariants = findFiles(glob: '**/Dockerfile')
                        echo """${containerVariants[0].name} ${containerVariants[0].path} ${containerVariants[0].directory} ${containerVariants[0].length} ${containerVariants[0].lastModified}"""
                        echo """${containerVariants[1].name} ${containerVariants[1].path} ${containerVariants[1].directory} ${containerVariants[1].length} ${containerVariants[1].lastModified}"""
                        // docker.withRegistry('https://registry-1.docker.io/v2/', 'dockerhub') {
                        //     def image = docker.build('ktaletsk/polus-notebook:jenkins-test', '--network=host --no-cache ./')
                        //     image.push()
                        // }
                    }
                }
            }
        }
    }
}