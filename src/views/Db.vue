<template>
  <b-container>
    <h1 v-if="dbLoading">Loading DB...</h1>
    <h1 v-else>DB loaded!</h1>
  </b-container>
</template>
<script>

import $api from '../api'
import Dexie from 'dexie'

export default {
  name: 'db',
  data() {
    return {
      datab: null,
      manifestLoading: true,
      manifestData: [],
      dbLoading: true,
      allData: [],
      clanMembersData: [],
      clanMembersLoading: true,
      clanMembers: [],
      clanMemberIds: [],
      error: '',
      errorManifest: '',
      errorClanMembers: '',
      fields: [
        {
          key: 'displayName',
          sortable: true
        },
        {
          key: 'joinDate',
          sortable: true
        },
        {
          key: 'triumph',
          sortable: true
        },
        {
          key: 'power',
          sortable: true
        },
        {
          key: 'lastPlayed',
          sortable: true,
          label: "Last Played"
        }
      ]
    }
  },
  methods: {
    fetchManifest() {
      $api.fetchManifest()
        .then(responseData => {
          this.manifestData.push(responseData)
          this.manifestLoading = false
          console.log('fetchManifest() done')
          this.fetchContent(responseData.Response.jsonWorldContentPaths.en)
        }).catch(error => {
          this.errorManifest = error.message
        })
    },
    fetchContent(content_url) {
      console.log('fetchContent() start')
      $api.fetchContent(content_url)
        .then(responseData => {
          //this.db.push(responseData);
          //localStorage.setItem('destinydata', JSON.stringify(responseData))
          //localStorage.setItem('activities', JSON.stringify(responseData.DestinyActivityDefinition))
          this.populateDb(responseData)
          console.log('fetchContent() finished')
          //this.fetchClanMembers()
        }).catch(error => {
          console.log('fetchContent ERROR ' + error)
        })
    },
    async populateDb(data) {
      console.log('populateDb() started')
      await this.datab.destinydata.add({data: data})
      console.log('populateDb() finished')
      //await this.datab.hashes.delete(12)
      //let p = await this.datab.hashes.get(11)
      //console.log(p)
      this.dbLoading = false
    },
    loopThroughClanMembers() {
      console.log('loopThroughClanMembers() starting')
      this.clanMemberIds.forEach(element => {
        $api.fetchProfile(element.membershipId, element.membershipType)
          .then(responseData => {
            if (responseData.ErrorCode != 1) {
              console.log(`${element.displayName} (${element.membershipId}) Error ${responseData.ErrorCode} - ${responseData.Message}`)
              return;
            }
            let player = this.clanMemberIds.find(obj => obj.membershipId == element.membershipId)

            for (const [key, value] of Object.entries(responseData.Response.characters.data)) {
              if (value.light > player["power"]) {
                player["power"] = value.light
              }
            }

            for (const [key, value] of Object.entries(responseData.Response.characterActivities.data)) {
              if (value.currentActivityHash != 0) {
                console.log(value.currentActivityHash)
              }
            }

            player["triumph"] = responseData.Response.profileRecords.data.score.toString()
            player["lastPlayed"] = responseData.Response.profile.data.dateLastPlayed
          }).catch(error => {
            console.log('loopThroughClanMembers: ' + error.message)
          })
      })

      console.log('loopThroughClanMembers finished')
    },
    fetchClanMembers() {

      // Retrieve all clan members
      $api.fetchClanMembers()
        .then(responseData => {
          this.clanMembersData.push(responseData)
          // Loop through each clan member
          responseData.Response.results.forEach(element => {
            this.clanMemberIds.push({
              "membershipType": element.destinyUserInfo.membershipType,
              "membershipId": element.destinyUserInfo.membershipId,
              "joinDate": element.joinDate,
              "displayName": element.destinyUserInfo.displayName,
              "triumph": 0,
              "power": 0,
              "lastPlayed": "never",
              })
          })
          console.log('fetchClanMembers() finished')
          this.loopThroughClanMembers()
          this.clanMembersLoading = false;
        }).catch(error => {
          this.errorClanMembers = error.message
        })
    },
    async setupDB() {
      console.log('setupDB() started')
      this.datab = new Dexie('destinyDb')

      this.datab.version(1).stores({
        destinydata: '++id, data'
      })

      this.datab.open().catch(function (err) {
          console.error (err.stack || err);
      });

      console.log('setupDB() finished')

      /*
      await this.datab.hashes.add({
        hash: 'hashvalue'
      })

      await this.datab.hashes
        .limit(5)
        .each(f => {
          console.log(f.hash)
      })
      */
    },
    async getDataTest() {
      console.log('getDataTest() start - checking if data already exists')
      let p = await this.datab.destinydata.limit(1).toArray()
      if (p === undefined || p.length == 0) {
        console.log('New data needs to be fetched')
        this.fetchManifest()
      } else {
        console.log('No new data needs to be fetched.')
        this.dbLoading = false
      }
      console.log('getDataTest() end')
    }
  },
  beforeMount() {
    this.setupDB()
    //this.fetchManifest()
    this.getDataTest()
  }
}
</script>

<style lang="scss">
h1 {
  color: white;
}

td {
  font-family: "nhg text";
}

h5 {
  font-family: "nhg display sub";
}

p, a {
  color: white;
  font-family: "nhg display sub";
}

th, td {
  color: white;
}
</style>
