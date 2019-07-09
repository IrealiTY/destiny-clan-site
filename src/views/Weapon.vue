<template>
    <b-contatiner fluid class="bg-dark">
      <b-row>
        <b-col>
        </b-col>
        <b-col class="weap-column">
          <h1 class="text-light"> {{ resources_weapon[0].name | allcaps }}</h1>
          <h3 class="text-light">{{ resources_weapon[0].gun_type | allcaps }}</h3>
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
      <b-row align-h="center">
        <div v-if="resources[0].length > 0">
        <b-table small class="w-50 text-light table-dark" :items="resources[0]" :fields="fields">
          <template slot="name" slot-scope="data">
            <router-link CLASS="txt" :to="{ name: 'player', params: { membership_id: data.item.membership_id }}"> {{ data.item.name }}</router-link>
          </template>
        </b-table>
        </div>
        <div v-else>
          <h1>No results</h1>
        </div>
      </b-row>
    </b-contatiner>
</template>

<script>
import $backend from '../backend'
import { error } from 'util';

export default {
  name: 'weapon',
  data() {
    return {
      loading: false,
      navIndex: 0,
      componentWeapon: 0,
      time_ranges: ['Last 24 Hours', 'Last 30 Days', 'Lifetime'],
      activeIndexDates: null,
      resources: [],
      resources_weapon: [],
      error: '',
      time_ranges: [
        { name: '24 Hours', time: 1 },
        { name: '3 Days', time: 3 },
        { name: '30 Days', time: 30 },
        { name: 'Lifetime', time: 0 }
      ],
      fields: [
        {
          key: 'name',
          sortable: true
        },
        {
          key: 'total_kills',
          label: 'Kills',
          sortable: true
        }
      ]
    }
  },
  filters: {
    allcaps: function(value) {
      return value.toUpperCase();
    }
  },
  methods: {
    changeTime(days, button_index) {
      this.activeIndexDates = button_index;
      this.fetchDestinyWeaponKills(this.$route.params.weapon_id, days);
    },
    fetchDestinyWeaponKills(weapon_id, days) {
      this.loading = true;
      $backend.fetchDestinyResourceWeaponKills(weapon_id, days)
        .then(responseData => {
          this.loading = false;
          this.resources = [];
          this.resources.push(responseData);
        }).catch(error => {
          this.error = error.message
        })
    },
    fetchDestinyWeapon(weapon_id) {
      $backend.fetchDestinyResourceWeapon(weapon_id)
        .then(responseData => {
          this.resources_weapon.push(responseData)
        }).catch(error => {
          this.error = error.message
        })
    }
  },
  beforeMount() {
    this.activeIndexDates = 3;
    this.fetchDestinyWeapon(this.$route.params.weapon_id);
    this.fetchDestinyWeaponKills(this.$route.params.weapon_id, 0);
  }
}
</script>

<style lang="scss">

h1, .txt {
  font-family: "nhg display";
}

h3 {
  font-family: "nhg display sub";
}

.navIndex a {
  color: #9ad3ff;
}
</style>