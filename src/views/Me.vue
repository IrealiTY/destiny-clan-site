<template>
  <b-container>
    <b-table :items="clanMemberIds" :fields="fields">
        <template slot="displayName" slot-scope="data">
          <router-link class="txt" :to="{ name: 'player', params: { membership_id: data.item.membershipId }}">{{ data.item.displayName }}</router-link>
        </template>
    </b-table>
  </b-container>
</template>
<script>

import $api from '../api'
import moment from 'moment'
import $dexie from '../database'
import Dexie from 'dexie'

export default {
  name: 'me',
  data() {
    return {
      datab: null,
      myDataRaw: [],
      clanMemberIds: [],
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
    async fetchActivityName(activity_hash) {
      console.log('fetchActivityName() starting indexedb query')
      //let p = await this.datab.destinydata.toCollection().first()
      let p = await this.datab.destinydata.limit(1).toArray()
      console.log('fetchActivityName() finishing indexedb query')
      let activityName = p[0].data.DestinyActivityDefinition[activity_hash].displayProperties.name
      console.log('fetchActivityName() found activity name: ' + activityName)
      return activityName
    },
    async dbInit() {
      this.datab = new Dexie('destinyDb')

      this.datab.version(1).stores({
        destinydata: '++id, data'
      })

      this.datab.open().catch(function (err) {
        console.error (err.stack || err);
      });

      await $dexie.setupDB()
    },
    async fillOutData(myResponseData) {
        console.log('fillOutData() start')
        let player = this.clanMemberIds.find(obj => obj.membershipId == myResponseData.Response.profile.data.userInfo.membershipId)
        let currentActivity

        console.log('fetchProfile() finding power')
        for (const [key, value] of Object.entries(myResponseData.Response.characters.data)) {
            if (value.light > player["power"]) {
                player["power"] = value.light
            }
        }

        console.log('fetchActivityName() finding acitivty name')
        for (const [key, value] of Object.entries(myResponseData.Response.characterActivities.data)) {
            if (value.currentActivityHash != 0) {
                currentActivity = await this.fetchActivityName(value.currentActivityHash)
                console.log('Current activity: ' + currentActivity)
            }
        }

        console.log('fetchActivityName() triumph')
        player["triumph"] = myResponseData.Response.profileRecords.data.score.toString()

        if (currentActivity) {
            player["lastPlayed"] = "Playing activity: " + currentActivity
        } else {
            player["lastPlayed"] = responseData.Response.profile.data.dateLastPlayed
        }
        console.log('fillOutData() end')
    },
    fetchMyProfile() {
        $api.fetchProfile('4611686018470721488', 4)
            .then(myResponseData => {
                this.myDataRaw.push(myResponseData)
                this.clanMemberIds.push({
                    "membershipType": myResponseData.Response.profile.data.userInfo.membershipType,
                    "membershipId": myResponseData.Response.profile.data.userInfo.membershipId,
                    "joinDate": "never",
                    "displayName": myResponseData.Response.profile.data.userInfo.displayName,
                    "triumph": 0,
                    "power": 0,
                    "lastPlayed": "never",
                })
                this.fillOutData(myResponseData)
                console.log('fetchProfile() finished')
            }).catch(error => {
                console.log('fetchMyProfile() error - ' + error.message)
            })
    }
  },
  beforeMount() {
    this.dbInit()
    this.fetchMyProfile()
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
