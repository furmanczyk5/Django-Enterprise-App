/*
planning_styles.js

Customized styles for our Django admin CKEditor instance

This would be added to the instance via something like:

CKEDITOR.stylesSet.add('planning_styles', planning_styles)

See the docs for more info
https://ckeditor.com/docs/ckeditor4/latest/guide/dev_howtos_styles.html
*/

const planning_styles = [
  {
    name: 'Regular',
    element: ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', 'p'],
    attributes: {'class': ''}
  },
  {
    name: 'Button (P)',
    element: ['a'],
    attributes: {'class': 'btn btn-primary'}
  },
  {
    name: 'Responsive',
    element: ['img'],
    attributes: {'class': 'img-responsive'}
  },
  {
    name: 'Underlined',
    element: ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
    attributes: {'class': 'headling-underline'}
  },
  {
    name: 'Small',
    element: ['p'],
    attributes: {'class': 'small'}
  }
];
