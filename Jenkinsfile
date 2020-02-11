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
            def containerVariants = sh(returnStdout: true, script: 'ls -d *').trim().split(System.getProperty("line.separator"))
            println """${containerVariants}"""

            // steps {
            //     dir('manifests') {
            //         script {
            //             def containerVariants = sh(returnStdout: true, script: 'ls -d *').trim().split(System.getProperty("line.separator"))
            //             containerVariants.each {
            //                 dir("""${it}""") {
            //                     println """Building container tag: ${it}"""
            //                     docker.withRegistry('https://registry-1.docker.io/v2/', 'dockerhub') {
            //                         def image = docker.build("""ktaletsk/polus-notebook:${it}""", '--network=host --no-cache ./')
            //                         image.push()
            //                     }
            //                 }
            //             }
            //         }
            //     }
            // }
        }
    }
}