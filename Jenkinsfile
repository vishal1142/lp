pipeline { 
    agent any   

    stages {
        stage('Git Checkout') {

            steps {

                script {
                    // Checkout the code from the specified branch of the Git repository
                    gitCheckout(
                        branch: "main",
                        url: "https://github.com/vishal1142/lp.git"
                }
            }
        }
    }
}
