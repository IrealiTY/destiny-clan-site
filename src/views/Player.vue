<template>
  <b-container fluid class="bg-dark">
    <b-row>
      <b-col>
      </b-col>
      <b-col>
        <h1 class="text-light">{{ resources_player[0].name | allcaps }}</h1>
        <h6 class="text-light">Last updated at {{ resources_player[0].last_played | momentize }}</h6>
        <br />
        <b-button-group size="sm">
          <b-button
            v-for="(btn, index) in time_ranges"
            :key="index"
            v-bind:class="{ active: activeIndexDates === index }"
            v-on:click="changeTime(btn.time, index)"
          >{{ btn.name }}
          </b-button>
        </b-button-group>
      </b-col>
      <b-col></b-col>
    </b-row>
    <br />
    <b-row>
      <b-col md="3" offset-md="3">
        <b-table small class="w-50 text-light table-dark" :key="componentKeyCharacters" :items="resources_chars[0]" :fields="fields_chars">
        </b-table>
      </b-col>
      <b-col md="3">
        <b-table small class="w-50 text-light table-dark" :key="componentKeyWeapons" :items="resources_weapons[0]" :fields="fields_weapons">
          <template slot="name" slot-scope="data">
            <router-link :to="{ name: 'weapon', params: { weapon_id: data.item.weapon_id }}"> {{ data.item.name }}</router-link>
          </template>
        </b-table>
      </b-col>
    </b-row>
  </b-container>
</template>

<script>
import $backend from '../backend'
import moment from 'moment'
import { error } from 'util';

export default {
  name: 'player',
  data() {
    return {
      navIndex: 0,
      componentKeyCharacters: 0,
      componentKeyWeapons: 0,
      resources_player: [],
      resources_chars: [],
      resources_weapons: [],
      activeIndexDates: null,
      time_ranges: [
        { name: '24 Hours', time: 1 },
        { name: '3 Days', time: 3 },
        { name: '30 Days', time: 30 },
        { name: 'Lifetime', time: 0 }
      ],
      error: '',
      fields_weapons: [
        {
          key: 'name',
          sortable: true
        },
        {
          key: 'total_kills',
          label: 'Kills',
          sortable: true
        }
      ],
      fields_chars: [
        {
          key: 'class_name',
          label: 'Character'
        },
        {
          key: 'total_kills',
          label: 'Kills'
        }
      ]
    }
  },
  filters: {
    momentize: function (value) {
        return moment(value).format('YYYY-MM-DD HH:mm:ss')
    },
    allcaps: function(value) {
      return value.toUpperCase();
    }
  },
  methods: {
    changeTime(days, button_index) {
      this.activeIndexDates = button_index;
      this.fetchDestinyPlayerCharacters(this.$route.params.membership_id, days);
      this.fetchDestinyPlayerWeapons(this.$route.params.membership_id, days);
    },
    fetchDestinyPlayer(membership_id) {
      $backend.fetchDestinyResourcePlayer(membership_id)
        .then(responseData => {
          this.resources_player.push(responseData)
        }).catch(error => {
          this.error = error.message
        })
    },
    fetchDestinyPlayerWeapons(membership_id, days) {
      $backend.fetchDestinyResourcePlayerWeapons(membership_id, days)
        .then(responseData => {
          this.resources_weapons = [];
          this.resources_weapons.push(responseData)
        }).catch(error => {
          this.error = error.message
        })
    },
    fetchDestinyPlayerCharacters(membership_id, days) {
      $backend.fetchDestinyResourcePlayerCharacters(membership_id, days)
        .then(responseData => {
          this.resources_chars = [];
          this.resources_chars.push(responseData)
        }).catch(error => {
          this.error = error.message
        })
    }
  },
  beforeMount() {
    this.activeIndexDates = 3;
    this.fetchDestinyPlayer(this.$route.params.membership_id);
    this.fetchDestinyPlayerWeapons(this.$route.params.membership_id, 0);
    this.fetchDestinyPlayerCharacters(this.$route.params.membership_id, 0);
  }
}
</script>

<style lang="scss">
h6 {
  font-family: "nhg display sub 2";
}

.navIndex a {
  color: #9ad3ff;
}
</style>
