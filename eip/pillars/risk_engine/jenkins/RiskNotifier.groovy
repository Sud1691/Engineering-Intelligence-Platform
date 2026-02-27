/**
 * Jenkins shared library step for sending deployment events to the
 * Engineering Intelligence Platform (EIP) Risk Engine webhook.
 *
 * Usage in a Jenkinsfile (declarative):
 *
 *   @Library('eip-shared-lib') _
 *
 *   post {
 *     success {
 *       eipRiskNotify(
 *         endpoint: 'https://eip.example.com/risk/webhook/jenkins',
 *         environment: 'production'
 *       )
 *     }
 *   }
 */

def call(Map config = [:]) {
  if (!config.endpoint) {
    error "eipRiskNotify: 'endpoint' is required"
  }

  def envName = config.environment ?: 'production'

  def payload = [
    service_name       : env.JOB_BASE_NAME,
    environment        : envName,
    branch             : env.BRANCH_NAME ?: env.GIT_BRANCH ?: 'unknown',
    commit_sha         : env.GIT_COMMIT ?: 'unknown',
    commit_message     : env.GIT_COMMIT_MESSAGE ?: '',
    commit_author      : env.GIT_AUTHOR_NAME ?: '',
    commit_author_email: env.GIT_AUTHOR_EMAIL ?: '',
    changed_files      : [],
    lines_added        : 0,
    lines_deleted      : 0,
    deploy_hour        : new Date().format('H',   TimeZone.getTimeZone('UTC')) as int,
    deploy_day         : new Date().format('u',   TimeZone.getTimeZone('UTC')) as int,
    build_url          : env.BUILD_URL,
    coverage_delta     : null,
  ]

  echo "Sending deployment event to EIP Risk Engine at ${config.endpoint}"

  httpRequest(
    httpMode           : 'POST',
    url                : config.endpoint,
    contentType        : 'APPLICATION_JSON',
    requestBody        : groovy.json.JsonOutput.toJson(payload),
    validResponseCodes : '100:399',
    ignoreSslErrors    : config.ignoreSslErrors ?: false
  )
}

