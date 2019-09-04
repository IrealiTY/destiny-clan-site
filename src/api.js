import axios from 'axios'

let $axios = axios.create({
  baseURL: 'https://www.bungie.net',
  timeout: 5000,
  headers: {'Content-Type': 'application/json', 'X-API-Key': 'fef8dc02aba245d5a9cc0c1ad0ea65ac'}
})

let $axios2 = axios.create({
  timeout: 60000,
  headers: {}
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
  async fetchProfile(membership_id, membershipType) {
    const response = await $axios.get(`Platform/Destiny2/${membershipType}/Profile/${membership_id}/?components=100,900,200,204`);
    return response.data;
  },
  
  async fetchManifest() {
    const response = await $axios.get(`Platform/Destiny2/Manifest/`);
    return response.data;
  },

  async fetchContent(content_url) {
    let url;
    if (process.env.VUE_APP_ENV === "dev") {
      url = '/bungie' + content_url
    } else if (process.env.VUE_APP_ENV === "stg") {
      url = '/bungie' + content_url
    } else {
      url = 'https://bungie.net' + content_url
    }
    const response = await $axios2.get(url)
    return response.data;
  },

  async fetchClanMembers() {
      const response = await $axios.get(`Platform/GroupV2/198175/Members/`);
      return response.data;
  },

  async fetchCharacters(membership_id, character_id) {
      const response = await $axios.get(`Platform/Destiny2/4/Profile/${membership_id}/Character/${character_id}/?components=200'`);
      return response.data;
  }
}
