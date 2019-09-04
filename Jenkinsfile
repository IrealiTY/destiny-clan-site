node('docker') {
    stage('Test') {
        checkout scm
        def testImage = docker.build("test-image", "-f ./docker/Dockerfile.tests .")
        try {
            testImage.inside {
                sh 'pytest tests/test_destiny.py'
            }
        }
        catch (exc) {
            sh """
                curl -H "Content-Type: application/json" -X POST -d '{"username": "Jenkins", "content": "[${env.JOB_BASE_NAME}] :x: Job failed during test pass. Log: https://jenkins.staging.lab/job/${env.JOB_BASE_NAME}/${env.BUILD_ID}/console"}' https://discordapp.com/webhook/url
            """

            throw exc
            error("Job failed.")
        }
    }
    
    stage('Deploy - Staging') {
        try {
            sh 'docker-compose -f ./docker/docker-compose.yml down'
            sh 'docker-compose -f ./docker/docker-compose.yml -p clan up -d --build'
        }
        catch (exc) {
            sh """
                curl -H "Content-Type: application/json" -X POST -d '{"username": "Jenkins", "content": "[${env.JOB_BASE_NAME}] :x: Job failed during deployment to staging. https://jenkins.staging.lab/job/${env.JOB_BASE_NAME}/${env.BUILD_ID}"}' https://discordapp.com/webhook/url
            """
            throw exc
            error("Job failed.")
        }
    }

    stage ('Post-deploy') {
        def currentResult = currentBuild.result ?: 'SUCCESS'
        def previousResult = currentBuild.getPreviousBuild()?.result
        println("Current result: ${currentResult} / Previous result: ${previousResult}")
        if (previousResult != null && previousResult != currentResult) {
            if (currentResult == 'SUCCESS') {
                sh """
                    curl -H "Content-Type: application/json" -X POST -d '{"username": "Jenkins", "content": "[${env.JOB_BASE_NAME}] :white_check_mark: Job is healthy again. https://jenkins.staging.lab/job/${env.JOB_BASE_NAME}/${env.BUILD_ID}"}' https://discordapp.com/webhook/url
                """
            }
        }
    }
}
