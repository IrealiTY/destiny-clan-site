import Dexie from 'dexie'
import $api from './api'

console.log('setupDB() started')
var datab = new Dexie('destinyDb')

datab.version(1).stores({
destinydata: '++id, data'
})

datab.open().catch(function (err) {
    console.error (err.stack || err);
});

console.log('setupDB() finished')

export default {
    async populateDb(data) {
        await datab.destinydata.add({data: data})
    },
    fetchManifest() {
        $api.fetchManifest()
          .then(responseData => {
            this.fetchContent(responseData.Response.jsonWorldContentPaths.en)
          }).catch(error => {
            console.log('fetchManifest ERROR ' + error)
          })
    },
    fetchContent(content_url) {
        $api.fetchContent(content_url)
          .then(responseData => {
            this.populateDb(responseData)
          }).catch(error => {
            console.log('fetchContent ERROR ' + error)
          })
    }, 
    async setupDB() {
        this.fetchDestinyData(datab)
    },
    async fetchDestinyData(data) {
        let p = await data.destinydata.limit(1).toArray()
        if (p === undefined || p.length == 0) {
          this.fetchManifest()
        } else {
        }
      }
}
