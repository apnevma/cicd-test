pipeline {
    agent { label 'agent-1' }
    
    environment {
        REGISTRY = 'harbor.avalanche.rid-intrasoft.eu'
        COMPONENT = 'demo'
        REGISTRY_IMAGE = "${REGISTRY}/${COMPONENT}/${COMPONENT}"
        DOCKERFILE_PATH = 'Dockerfile'
        CURRENT_BUILD_NUMBER = "${currentBuild.number}"
        IMAGE_TAG = "jenkins-${CURRENT_BUILD_NUMBER}"
        REGISTRY_USER = credentials('RobotName')
        REGISTRY_PASSWORD = credentials('RobotSecret')
        HEALTH_URL = 'http://localhost:8002/health'
    }
    
    stages {
        stage('Checkout Code') {
            steps {
                echo 'Code checkout handled automatically by Jenkins SCM'
                sh 'ls -la'
            }
        }

        stage('SonarQube Analysis') {
            steps {
                script {
                    scannerHome = tool 'SonarScanner'  // ← Must match SonarQube tool name setup in jenkins
                }
                withSonarQubeEnv('SonarServer') {      // ← Must match SonarQube server name setup in jenkins
                    sh "${scannerHome}/bin/sonar-scanner"
                }
            }
        }
        
        stage('Build Container Image') {
            steps {
                echo 'Building container image'
                sh "docker build --network=host -t ${REGISTRY_IMAGE}:${IMAGE_TAG} -f ${DOCKERFILE_PATH} ."
                echo "Image built: ${REGISTRY_IMAGE}:${IMAGE_TAG}"
            }
        }
        
        stage('Test Container Image') {
            steps {
                echo 'Starting container for testing'
                sh "docker run -d --name ${COMPONENT}-test -p 8003:8000 ${REGISTRY_IMAGE}:${IMAGE_TAG}"
                
                echo 'Waiting for test container to start...'
                sleep(time: 5, unit: 'SECONDS')
                
                echo 'Running health check on test container'
                script {
                    def testUrl = 'http://localhost:8003/health'
                    def response = sh(
                        script: "curl -s -o /dev/null -w '%{http_code}' ${testUrl}",
                        returnStdout: true
                    ).trim()
                    
                    if (response == '200') {
                        echo "✓ Test passed! Container is healthy (HTTP ${response})"
                        sh "curl -s ${testUrl}"
                    } else {
                        error "✗ Test failed! Expected 200, got ${response}"
                    }
                }
                
                echo 'Stopping and removing test container'
                sh "docker stop ${COMPONENT}-test"
                sh "docker rm ${COMPONENT}-test"
                
                echo '✓ Image testing completed successfully'
            }
        }
        
        stage('Push Container Image to Harbor Registry') {
            steps {
                echo 'Logging in to Harbor registry'
                sh 'docker login ${REGISTRY} -u ${REGISTRY_USER} -p ${REGISTRY_PASSWORD}'
                
                echo 'Pushing image to registry'
                sh "docker push ${REGISTRY_IMAGE}:${IMAGE_TAG}"
                
                echo 'Image pushed successfully'
            }
        }
        
        stage('Stop Existing Container') {
            steps {
                echo 'Stopping and removing existing containers'
                sh '''
                    if [ $( docker ps -a -f name=$COMPONENT | grep $COMPONENT | wc -l ) -eq 1 ]; then
                        echo "Container exists - stopping and removing"
                        docker stop $COMPONENT
                        docker rm $COMPONENT
                    else
                        echo "No existing container found"
                    fi
                '''
                // Alternative: Using docker-compose
                // sh 'docker-compose down || true'
            }
        }
        
        stage('Deploy Container') {
            steps {
                echo 'Pulling container image from registry'
                sh "docker pull ${REGISTRY_IMAGE}:${IMAGE_TAG}"
                
                echo 'Deploying container'
                sh "docker run -d --name ${COMPONENT} -p 8002:8000 ${REGISTRY_IMAGE}:${IMAGE_TAG}"
                
                // Alternative: Using docker-compose with image from registry
                // Update docker-compose.yml to use: image: ${REGISTRY_IMAGE}:${IMAGE_TAG}
                // sh 'docker-compose up -d'
            }
        }
        
        stage('Health Check') {
            steps {
                echo 'Waiting for service to start...'
                sleep(time: 10, unit: 'SECONDS')
                
                echo 'Checking service health'
                script {
                    def response = sh(
                        script: "curl -s -o /dev/null -w '%{http_code}' ${HEALTH_URL}",
                        returnStdout: true
                    ).trim()
                    
                    if (response == '200') {
                        echo "✓ Health check passed! Service is healthy (HTTP ${response})"
                    } else {
                        error "✗ Health check failed! Expected 200, got ${response}"
                    }
                }
                
                // Show health check response
                sh "curl -s ${HEALTH_URL} | python3 -m json.tool || curl ${HEALTH_URL}"
            }
        }
        
        stage('Clean Up') {
            steps {
                echo 'Logging out from Harbor registry'
                sh "docker logout ${REGISTRY}"
                
                // Optional: Remove local image to save space
                // sh "docker rmi ${REGISTRY_IMAGE}:${IMAGE_TAG} || true"
            }
        }
    }
    
    post {
        success {
            echo "✓ Pipeline completed successfully!"
            echo "Service deployed: ${REGISTRY_IMAGE}:${IMAGE_TAG}"
            echo "Service is healthy and running at ${HEALTH_URL}"
        }
        failure {
            echo '✗ Pipeline failed. Check logs for details.'
            // Optional: Rollback
            // sh 'docker stop $COMPONENT || true'
            // sh 'docker rm $COMPONENT || true'
        }
        always {
            echo "Build Number: ${env.CURRENT_BUILD_NUMBER}"
            echo "Image Tag: ${env.IMAGE_TAG}"
        }
    }
}