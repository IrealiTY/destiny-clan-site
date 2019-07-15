node('docker') {
    stage('Test') {
        checkout scm
        def testImage = docker.build("test-image:${env.BUILD_ID}", "-f Dockerfile.tests .")
        try {
            testImage.inside {
                sh 'pytest tests/test_destiny.py'
            }
        }
        catch (exc) {
            node('master') {
                sh """
                    curl -H "Content-Type: application/json" -X POST -d '{"username": "Jenkins", "content": ":x: Build failed. Log: https://jenkins.lab.local/job/destiny-clan-site/${env.BUILD_ID}/console"}' https://discordapp.com/webhook/url
                """
            }

            throw exc
        }
        finally {
            def currentResult = currentBuild.result ?: 'SUCCESS'
            def previousResult = currentBuild.getPreviousBuild()?.result
            println("Current result: ${currentResult} / Previous result: ${previousResult}")
            if (previousResult != null && previousResult != currentResult) {
                if (currentResult == 'SUCCESS') {
                    sh """
                        curl -H "Content-Type: application/json" -X POST -d '{"username": "Jenkins", "content": ":white_check_mark: Build is healthy again"}' https://discordapp.com/webhook/url
                    """
                }
            }
        }
    }
}
