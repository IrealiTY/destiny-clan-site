import axios from 'axios'

let $axios = axios.create({
  baseURL: process.env.VUE_APP_API_ENDPOINT,
  timeout: 5000,
  headers: {'Content-Type': 'application/json'}
})

// Request Interceptor
$axios.interceptors.request.use(function (config) {
  config.headers['Authorization'] = 'Fake Token'
  return config
})

// Response Interceptor to handle and log errors
$axios.interceptors.response.use(function (response) {
  return response
}, function (error) {
  // Handle Error
  console.log(error)
  return Promise.reject(error)
})

export default {

  fetchResource () {
    return $axios.get(`resource/xxx`)
      .then(response => response.data)
  },

  fetchSecureResource () {
    return $axios.get(`secure-resource/zzz`)
      .then(response => response.data)
  },

  fetchDestinyResource () {
    return $axios.get(`resource/player`)
      .then(response => response.data)
  },

  fetchDestinyResourcePlayers () {
    return $axios.get(`resource/players`)
      .then(response => response.data)
  },

  fetchDestinyResourceRoster() {
    return $axios.get(`resources/roster`)
      .then(response => response.data)
  },
  fetchDestinyResourcePlayer(membership_id) {
    return $axios.get(`resources/player/${membership_id}`)
      .then(response => response.data)
  },
  async fetchDestinyResourcePlayerWeapons(membership_id, days) {
    const response = await $axios.get(`resources/player/${membership_id}/weapons/${days}`);
    return response.data;
  },
  async fetchDestinyResourcePlayerCharacters(membership_id, days) {
    const response = await $axios.get(`resources/player/${membership_id}/characters/${days}`);
    return response.data;
  },
  async fetchDestinyResourceWeapon(weapon_id) {
    const response = await $axios.get(`resources/weapon/${weapon_id}`);
    return response.data;
  },
  async fetchDestinyResourceWeaponKills(weapon_id, days) {
    const response = await $axios.get(`resources/weapon/${weapon_id}/kills/${days}`);
    return response.data;
  },
  async fetchDestinyResourceWeaponTypeKills(weapon_type, days) {
    const response = await $axios.get(`resources/weapontypes/${weapon_type}/${days}`);
    return response.data;
  },
  async fetchDestinyResourceWeaponCategoryKills(category, days) {
    const response = await $axios.get(`resources/weapons/${category}/${days}`);
    return response.data;
  },
  async fetchDestinyCollectible(collectible_hash) {
    const response = await $axios.get(`resources/collectible/${collectible_hash}`);
    return response.data;
  },
  async fetchDestinyCollectibles() {
    const response = await $axios.get(`resources/collectibles`);
    return response.data;
  },
  async fetchDestinyCollectiblesUnowned() {
    const response = await $axios.get(`resources/collectibles/unowned`);
    return response.data;
  }
}
