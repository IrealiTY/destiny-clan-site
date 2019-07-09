const VuetifyLoaderPlugin = require('vuetify-loader/lib/plugin')
module.exports = {
    configureWebpack: {
        plugins: [
          new VuetifyLoaderPlugin()
        ]
    },
    outputDir: 'dist',
    assetsDir: 'static',
    devServer: {
        proxy: {
            '/api*': {
                target: 'http://localhost:5000/'
            },
            '/bungie': {
                target: 'https://www.bungie.net/',
                changeOrigin: true,
                pathRewrite: {
                    '^/bungie': ''
                }
            }
        }
    }
}