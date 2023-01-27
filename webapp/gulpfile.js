const gulp = require('gulp');
const sass = require('gulp-sass')(require('sass'));
const babel = require('gulp-babel');
const livereload = require('gulp-livereload');

function html() {
  console.log("html: reloading...");
  return gulp.src('src/*.html')
        .pipe(gulp.dest('dist/'))
        .pipe(livereload());
}

function css() {
  console.log("scss: transpiling...");
  return gulp.src('src/scss/*.scss')
        .pipe(sass().on('error', sass.logError))
        .pipe(gulp.dest('dist/css/'))
	.pipe(livereload());
}

function js() {
  console.log("es: transpiling...");
  return gulp.src('src/es/*.js')
        .pipe(babel({ presets: ['@babel/env'] }))
        .pipe(gulp.dest('dist/js/'))
	.pipe(livereload());
}

exports.default = function() {
  livereload.listen();
  gulp.watch('src/*.html', html);
  gulp.watch('src/scss/*.scss', css);
  gulp.watch('src/es/*.js', js);
};
